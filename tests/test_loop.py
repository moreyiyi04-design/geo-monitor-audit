import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.aris_geo.loop import GeoLoop, Phase, PhaseOutcome
from tools.aris_geo.state import load_state
from tools.geo_loop import main


REPO_ROOT = Path(__file__).resolve().parents[1]
GEO_LOOP_SCRIPT = REPO_ROOT / "tools" / "geo_loop.py"


class GeoLoopTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-loop-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        (self.repo_root / ".git").mkdir(parents=True)
        (self.repo_root / "wiki" / "raw" / "demo").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "wiki" / "raw" / "demo" / "evidence.md").write_text(
            "# Demo evidence\n",
            encoding="utf-8",
        )
        (self.repo_root / "wiki" / "raw" / "broken").mkdir(parents=True)
        (self.repo_root / "wiki" / "raw" / "broken" / "evidence.md").write_text(
            "# Broken evidence\n",
            encoding="utf-8",
        )
        (self.repo_root / "wiki" / "queue.json").write_text(
            json.dumps(["broken", "demo"], ensure_ascii=False),
            encoding="utf-8",
        )

    def test_run_product_advances_through_explicit_phase_order_and_persists_pass(self):
        # Break caught: orchestration skips or reorders phases and never lands in a persisted PASS state.
        seen = []

        def handler(phase):
            def run(slug, state):
                seen.append((phase.value, slug, state.round))
                return PhaseOutcome(success=True, tokens=5)

            return run

        loop = GeoLoop(
            self.repo_root,
            phase_handlers={
                Phase.PLAN_QUERIES: handler(Phase.PLAN_QUERIES),
                Phase.FETCH: handler(Phase.FETCH),
                Phase.DIGEST: handler(Phase.DIGEST),
                Phase.PROFILE: handler(Phase.PROFILE),
                Phase.VENDOR_SKEPTIC: handler(Phase.VENDOR_SKEPTIC),
                Phase.ARBITER: handler(Phase.ARBITER),
                Phase.APPLY: handler(Phase.APPLY),
                Phase.VERIFY: handler(Phase.VERIFY),
                Phase.COMPILE: handler(Phase.COMPILE),
            },
        )

        result = loop.run_product("demo")

        self.assertTrue(result.ok)
        self.assertEqual("passed", result.status)
        self.assertEqual(
            [
                ("plan_queries", "demo", 0),
                ("fetch", "demo", 0),
                ("digest", "demo", 0),
                ("profile", "demo", 0),
                ("vendor_skeptic", "demo", 1),
                ("arbiter", "demo", 1),
                ("apply", "demo", 1),
                ("verify", "demo", 1),
                ("compile", "demo", 1),
            ],
            seen,
        )
        state = load_state(self.repo_root, "demo")
        self.assertEqual(Phase.PASS, state.phase)
        self.assertEqual(1, state.round)
        self.assertEqual(45, state.cost_so_far)
        self.assertIsNone(state.last_error)

    def test_run_product_skips_passed_slug_when_evidence_fingerprint_is_unchanged(self):
        # Break caught: completed products rerun every time even when the evidence tree is identical.
        seen = []

        def handler(slug, state):
            seen.append((slug, state.phase.value))
            return PhaseOutcome(success=True, tokens=1)

        handlers = {
            Phase.PLAN_QUERIES: handler,
            Phase.FETCH: handler,
            Phase.DIGEST: handler,
            Phase.PROFILE: handler,
            Phase.VENDOR_SKEPTIC: handler,
            Phase.ARBITER: handler,
            Phase.APPLY: handler,
            Phase.VERIFY: handler,
            Phase.COMPILE: handler,
        }
        loop = GeoLoop(self.repo_root, phase_handlers=handlers)

        first = loop.run_product("demo")
        seen.clear()
        second = loop.run_product("demo")

        self.assertEqual("passed", first.status)
        self.assertEqual("skipped", second.status)
        self.assertEqual([], seen)

    def test_run_product_restarts_from_profile_when_evidence_changes_after_pass(self):
        # Break caught: pass-skipping ignores changed evidence and leaves stale downstream output in place.
        seen = []

        def handler(slug, state):
            seen.append((state.phase.value, state.round))
            return PhaseOutcome(success=True, tokens=1)

        handlers = {
            Phase.PLAN_QUERIES: handler,
            Phase.FETCH: handler,
            Phase.DIGEST: handler,
            Phase.PROFILE: handler,
            Phase.VENDOR_SKEPTIC: handler,
            Phase.ARBITER: handler,
            Phase.APPLY: handler,
            Phase.VERIFY: handler,
            Phase.COMPILE: handler,
        }
        loop = GeoLoop(self.repo_root, phase_handlers=handlers)

        loop.run_product("demo")
        seen.clear()
        (self.repo_root / "wiki" / "raw" / "demo" / "evidence.md").write_text(
            "# Demo evidence changed\n",
            encoding="utf-8",
        )

        result = loop.run_product("demo")

        self.assertEqual("passed", result.status)
        self.assertEqual(
            [
                ("plan_queries", 0),
                ("fetch", 0),
                ("digest", 0),
                ("profile", 0),
                ("vendor_skeptic", 1),
                ("arbiter", 1),
                ("apply", 1),
                ("verify", 1),
                ("compile", 1),
            ],
            seen,
        )

    def test_run_product_retries_review_at_most_three_rounds_before_recording_failure(self):
        # Break caught: failed verification loops forever instead of stopping after the bounded review budget.
        seen = []

        def profile(slug, state):
            seen.append((state.phase.value, state.round))
            return PhaseOutcome(success=True, tokens=1)

        def review(slug, state):
            seen.append((state.phase.value, state.round))
            return PhaseOutcome(success=True, tokens=1)

        def verify(slug, state):
            seen.append((state.phase.value, state.round))
            return PhaseOutcome(success=False, tokens=1, error="verification failed", retry_review=True)

        loop = GeoLoop(
            self.repo_root,
            phase_handlers={
                Phase.PLAN_QUERIES: profile,
                Phase.FETCH: profile,
                Phase.DIGEST: profile,
                Phase.PROFILE: profile,
                Phase.VENDOR_SKEPTIC: review,
                Phase.ARBITER: review,
                Phase.APPLY: review,
                Phase.VERIFY: verify,
                Phase.COMPILE: review,
            },
        )

        result = loop.run_product("demo")

        self.assertFalse(result.ok)
        self.assertEqual("failed", result.status)
        self.assertEqual(
            [
                ("plan_queries", 0),
                ("fetch", 0),
                ("digest", 0),
                ("profile", 0),
                ("vendor_skeptic", 1),
                ("arbiter", 1),
                ("apply", 1),
                ("verify", 1),
                ("vendor_skeptic", 2),
                ("arbiter", 2),
                ("apply", 2),
                ("verify", 2),
                ("vendor_skeptic", 3),
                ("arbiter", 3),
                ("apply", 3),
                ("verify", 3),
            ],
            seen,
        )
        state = load_state(self.repo_root, "demo")
        self.assertEqual(Phase.VERIFY, state.phase)
        self.assertEqual(3, state.round)
        self.assertEqual("verification failed", state.last_error)

    def test_run_product_stops_before_next_phase_when_budget_is_exhausted(self):
        # Break caught: a product keeps invoking later phase handlers even after consuming the remaining token budget.
        seen = []

        def make_handler(phase, tokens):
            def handler(slug, state):
                seen.append(phase.value)
                return PhaseOutcome(success=True, tokens=tokens)

            return handler

        loop = GeoLoop(
            self.repo_root,
            phase_handlers={
                Phase.PLAN_QUERIES: make_handler(Phase.PLAN_QUERIES, 3),
                Phase.FETCH: make_handler(Phase.FETCH, 2),
                Phase.DIGEST: make_handler(Phase.DIGEST, 1),
                Phase.PROFILE: make_handler(Phase.PROFILE, 1),
                Phase.VENDOR_SKEPTIC: make_handler(Phase.VENDOR_SKEPTIC, 1),
                Phase.ARBITER: make_handler(Phase.ARBITER, 1),
                Phase.APPLY: make_handler(Phase.APPLY, 1),
                Phase.VERIFY: make_handler(Phase.VERIFY, 1),
                Phase.COMPILE: make_handler(Phase.COMPILE, 1),
            },
        )

        result = loop.run_product("demo", budget_tokens=5)

        self.assertFalse(result.ok)
        self.assertEqual("budget_exhausted", result.status)
        self.assertEqual(5, result.tokens)
        self.assertEqual(["plan_queries", "fetch"], seen)
        state = load_state(self.repo_root, "demo")
        self.assertEqual(Phase.DIGEST, state.phase)
        self.assertEqual("budget exhausted before phase: digest", state.last_error)

    def test_run_queue_continues_to_next_slug_after_a_failure(self):
        # Break caught: one broken product blocks the rest of the queue instead of recording the error and continuing.
        seen = []

        def profile(slug, state):
            seen.append((slug, state.phase.value))
            if slug == "broken" and state.phase is Phase.PROFILE:
                return PhaseOutcome(success=False, error="profile missing")
            return PhaseOutcome(success=True, tokens=1)

        def review(slug, state):
            seen.append((slug, state.phase.value))
            return PhaseOutcome(success=True, tokens=1)

        loop = GeoLoop(
            self.repo_root,
            phase_handlers={
                Phase.PLAN_QUERIES: profile,
                Phase.FETCH: profile,
                Phase.DIGEST: profile,
                Phase.PROFILE: profile,
                Phase.VENDOR_SKEPTIC: review,
                Phase.ARBITER: review,
                Phase.APPLY: review,
                Phase.VERIFY: review,
                Phase.COMPILE: review,
            },
        )

        outcomes = loop.run_queue()

        self.assertEqual(["broken", "demo"], [outcome.slug for outcome in outcomes])
        self.assertEqual(["failed", "passed"], [outcome.status for outcome in outcomes])
        self.assertEqual("profile missing", load_state(self.repo_root, "broken").last_error)
        self.assertEqual(Phase.PASS, load_state(self.repo_root, "demo").phase)
        self.assertEqual(
            [
                ("broken", "plan_queries"),
                ("broken", "fetch"),
                ("broken", "digest"),
                ("broken", "profile"),
                ("demo", "plan_queries"),
                ("demo", "fetch"),
                ("demo", "digest"),
                ("demo", "profile"),
                ("demo", "vendor_skeptic"),
                ("demo", "arbiter"),
                ("demo", "apply"),
                ("demo", "verify"),
                ("demo", "compile"),
            ],
            seen,
        )

    def test_run_queue_continues_after_missing_raw_evidence_directory(self):
        # Break caught: a missing evidence tree crashes the queue before later valid products can run.
        shutil.rmtree(self.repo_root / "wiki" / "raw" / "broken")
        seen = []

        def handler(slug, state):
            seen.append((slug, state.phase.value))
            return PhaseOutcome(success=True, tokens=1)

        loop = GeoLoop(
            self.repo_root,
            phase_handlers={phase: handler for phase in (
                Phase.PLAN_QUERIES,
                Phase.FETCH,
                Phase.DIGEST,
                Phase.PROFILE,
                Phase.VENDOR_SKEPTIC,
                Phase.ARBITER,
                Phase.APPLY,
                Phase.VERIFY,
                Phase.COMPILE,
            )},
        )

        outcomes = loop.run_queue()

        self.assertEqual(["failed", "passed"], [outcome.status for outcome in outcomes])
        self.assertEqual("missing raw evidence directory", load_state(self.repo_root, "broken").last_error)
        self.assertTrue(any(slug == "demo" for slug, _phase in seen))

    def test_run_queue_continues_after_corrupt_state_file(self):
        # Break caught: invalid persisted state JSON aborts the queue instead of isolating the failure to that slug.
        (self.repo_root / "wiki" / "state").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "wiki" / "state" / "broken.json").write_text("{not json", encoding="utf-8")
        seen = []

        def handler(slug, state):
            seen.append((slug, state.phase.value))
            return PhaseOutcome(success=True, tokens=1)

        loop = GeoLoop(
            self.repo_root,
            phase_handlers={phase: handler for phase in (
                Phase.PLAN_QUERIES,
                Phase.FETCH,
                Phase.DIGEST,
                Phase.PROFILE,
                Phase.VENDOR_SKEPTIC,
                Phase.ARBITER,
                Phase.APPLY,
                Phase.VERIFY,
                Phase.COMPILE,
            )},
        )

        outcomes = loop.run_queue()

        self.assertEqual(["failed", "passed"], [outcome.status for outcome in outcomes])
        self.assertEqual("invalid state JSON for broken", load_state(self.repo_root, "broken").last_error)
        self.assertTrue(any(slug == "demo" for slug, _phase in seen))


class GeoLoopCliTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-loop-cli-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        (self.repo_root / ".git").mkdir(parents=True)
        (self.repo_root / "wiki" / "raw" / "demo").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "wiki" / "raw" / "demo" / "evidence.md").write_text(
            "# Demo evidence\n",
            encoding="utf-8",
        )
        (self.repo_root / "wiki" / "queue.json").write_text('["broken", "demo"]', encoding="utf-8")

    def test_main_rejects_non_positive_bounds(self):
        # Break caught: invalid zero/negative driver bounds are silently accepted and misconfigure the loop.
        for argv in (
            ["--limit", "0"],
            ["--budget-tokens", "-1"],
            ["--parallel", "0"],
            ["--refresh-stale", "0"],
        ):
            with self.subTest(argv=argv):
                with self.assertRaisesRegex(SystemExit, "2"):
                    main(argv)

    def test_main_rejects_parallel_greater_than_one_until_parallel_execution_exists(self):
        # Break caught: the CLI advertises parallel workers while still running sequentially.
        exit_code = main(["--repo-root", str(self.repo_root), "--parallel", "2"])

        self.assertEqual(2, exit_code)

    def test_main_builds_live_handlers_from_cli_options(self):
        # Break caught: --live ignores config/model/aris options and still runs the empty offline handler set.
        seen = {}
        (self.repo_root / "wiki" / "queue.json").write_text('["demo"]', encoding="utf-8")
        (self.repo_root / "wiki" / "raw" / "demo").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "wiki" / "raw" / "demo" / "bootstrap.txt").write_text("seed\n", encoding="utf-8")
        (self.repo_root / "wiki" / "sources.json").write_text(
            json.dumps(
                {
                    "products": [
                        {
                            "slug": "demo",
                            "name": "Demo Product",
                            "market": "overseas",
                            "category": ["监测/可见性追踪"],
                            "openness": "closed",
                            "urls": [],
                        }
                    ]
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        def live_handler_builder(repo_root, **kwargs):
            seen["repo_root"] = repo_root
            seen["kwargs"] = kwargs
            return {
                phase: (lambda _slug, _state: PhaseOutcome(success=True, tokens=0))
                for phase in (
                    Phase.PLAN_QUERIES,
                    Phase.FETCH,
                    Phase.DIGEST,
                    Phase.PROFILE,
                    Phase.VENDOR_SKEPTIC,
                    Phase.ARBITER,
                    Phase.APPLY,
                    Phase.VERIFY,
                    Phase.COMPILE,
                )
            }

        exit_code = main(
            [
                "--repo-root",
                str(self.repo_root),
                "--live",
                "--config",
                str(self.repo_root / "wiki" / "sources.json"),
                "--model",
                "deepseek-v4-flash",
                "--aris-bin",
                "/tmp/fake-aris",
            ],
            live_handler_builder=live_handler_builder,
        )

        self.assertEqual(0, exit_code)
        self.assertEqual(self.repo_root, seen["repo_root"])
        self.assertEqual(self.repo_root / "wiki" / "sources.json", seen["kwargs"]["config_path"])
        self.assertEqual("deepseek-v4-flash", seen["kwargs"]["model"])
        self.assertEqual("/tmp/fake-aris", seen["kwargs"]["aris_bin"])

    def test_geo_loop_script_returns_one_and_stderr_when_outcomes_fail(self):
        # Break caught: direct CLI runs with missing handlers exit 0 and look successful.
        result = subprocess.run(
            [sys.executable, str(GEO_LOOP_SCRIPT), "--repo-root", str(self.repo_root)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("broken: failed", result.stderr)
        self.assertIn("demo: failed", result.stderr)

    def test_geo_loop_script_help_runs_from_repo_root(self):
        # Break caught: running the script directly from the repo root crashes before argparse help.
        result = subprocess.run(
            [sys.executable, str(GEO_LOOP_SCRIPT), "--help"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("usage:", result.stdout)


if __name__ == "__main__":
    unittest.main()
