import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.aris_geo.state import Phase, ProductState, evidence_fingerprint, load_state, save_state


class StatePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-state-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        (self.repo_root / "wiki" / "raw" / "demo").mkdir(parents=True)
        (self.repo_root / "wiki" / "state").mkdir(parents=True)
        (self.repo_root / "wiki" / "raw" / "demo" / "evidence.md").write_text(
            "# Evidence\n",
            encoding="utf-8",
        )

    def test_load_state_returns_default_for_missing_state_file(self):
        # Break caught: a missing state file crashes resume instead of starting from the first phase.
        state = load_state(self.repo_root, "demo")

        self.assertEqual(
            ProductState(
                slug="demo",
                phase=Phase.PLAN_QUERIES,
                round=0,
                cost_so_far=0,
                last_error=None,
                evidence_fingerprint=None,
            ),
            state,
        )

    def test_save_state_replaces_json_atomically_without_leaving_temp_files(self):
        # Break caught: persistence rewrites state non-atomically and leaves temp files behind after updates.
        first = ProductState(
            slug="demo",
            phase=Phase.VENDOR_SKEPTIC,
            round=1,
            cost_so_far=13,
            last_error=None,
            evidence_fingerprint="fp-1",
        )
        second = ProductState(
            slug="demo",
            phase=Phase.PASS,
            round=2,
            cost_so_far=21,
            last_error=None,
            evidence_fingerprint="fp-2",
        )

        save_state(self.repo_root, first)
        save_state(self.repo_root, second)

        state_path = self.repo_root / "wiki" / "state" / "demo.json"
        self.assertEqual(second, load_state(self.repo_root, "demo"))
        self.assertEqual(
            {
                "slug": "demo",
                "phase": "pass",
                "round": 2,
                "cost_so_far": 21,
                "last_error": None,
                "evidence_fingerprint": "fp-2",
            },
            json.loads(state_path.read_text(encoding="utf-8")),
        )
        self.assertEqual([], list(state_path.parent.glob(".demo.json.*.tmp")))

    def test_load_state_rejects_persisted_slug_mismatch(self):
        # Break caught: a state file for one slug is silently loaded for another and can later overwrite the wrong product state.
        state_path = self.repo_root / "wiki" / "state" / "demo.json"
        state_path.write_text(
            json.dumps(
                {
                    "slug": "other",
                    "phase": "profile",
                    "round": 1,
                    "cost_so_far": 8,
                    "last_error": None,
                    "evidence_fingerprint": "fp-1",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "state slug mismatch for demo"):
            load_state(self.repo_root, "demo")


class EvidenceFingerprintTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-fingerprint-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        raw_dir = self.repo_root / "wiki" / "raw" / "demo"
        raw_dir.mkdir(parents=True)
        (raw_dir / "evidence.md").write_text("alpha\n", encoding="utf-8")
        (raw_dir / "snapshot.txt").write_text("beta\n", encoding="utf-8")

    def test_evidence_fingerprint_is_stable_for_same_tree_and_changes_when_any_file_changes(self):
        # Break caught: pass-skipping keys off unstable ordering or misses edits in the evidence tree.
        first = evidence_fingerprint(self.repo_root, "demo")
        second = evidence_fingerprint(self.repo_root, "demo")

        (self.repo_root / "wiki" / "raw" / "demo" / "snapshot.txt").write_text(
            "gamma\n",
            encoding="utf-8",
        )
        third = evidence_fingerprint(self.repo_root, "demo")

        self.assertEqual(first, second)
        self.assertNotEqual(first, third)


if __name__ == "__main__":
    unittest.main()
