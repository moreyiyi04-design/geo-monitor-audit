import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.aris_geo.grading import final_grade
from tools.aris_geo.scoring import calculate_scores, derive_auto_risk_flags


REPO_ROOT = Path(__file__).resolve().parents[1]
VERIFY_SCRIPT = REPO_ROOT / "tools" / "verify_evidence.py"
SCORE_SCRIPT = REPO_ROOT / "tools" / "score.py"


def envelope(value, source_ids=(), confidence="stated", note=None):
    record = {"v": value, "src": list(source_ids), "conf": confidence}
    if note is not None:
        record["note"] = note
    return record


class GateCliTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-cli-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        (self.repo_root / ".git").mkdir(parents=True)
        (self.repo_root / "wiki" / "products").mkdir(parents=True)
        (self.repo_root / "wiki" / "raw" / "demo").mkdir(parents=True)
        self.profile_path = self.repo_root / "wiki" / "products" / "demo.json"
        digest = self._write_excerpt("wiki/raw/demo/e1.txt", "Independent benchmark excerpt")
        self.base_profile = {
            "schema_version": "v1",
            "slug": "demo",
            "name_cn": envelope("演示产品", ["e1"]),
            "name_en": envelope("Demo", ["e1"]),
            "homepage": envelope("https://vendor.example", ["e1"]),
            "vendor_domains": ["vendor.example"],
            "category": ["监测/可见性追踪"],
            "measurement": {
                "capture_channel": envelope("browser", ["e1"]),
                "samples_per_prompt": envelope(3, ["e1"]),
                "reports_confidence_interval": envelope(True, ["e1"]),
                "declares_noise_floor": envelope(True, ["e1"]),
                "model_version_pinning": envelope(True, ["e1"]),
                "sov_formula_public": envelope(True, ["e1"]),
            },
            "mechanism": {
                "data_source": envelope("browser panels", ["e1"]),
            },
            "pricing": {
                "has_public_pricing": envelope(True, ["e1"]),
                "entry_engines": envelope(2, ["e1"]),
                "entry_seats": envelope(3, ["e1"]),
                "entry_prompts": envelope(500, ["e1"]),
                "min_commit": envelope("3 months", ["e1"]),
                "annual_only": envelope(False, ["e1"]),
                "trial": envelope(True, ["e1"]),
                "refund_terms": envelope("公开", ["e1"]),
                "unit_inflation_risk": envelope(False, ["e1"]),
            },
            "entity": {
                "registry_verifiable": envelope(True, ["e1"]),
                "team_public": envelope(True, ["e1"]),
            },
            "exit": {
                "data_export": envelope(True, ["e1"]),
                "history_portable": envelope(True, ["e1"]),
                "content_hosted_by_vendor": envelope(False, ["e1"]),
                "contract_lock": envelope("3 months", ["e1"]),
            },
            "evidence": [
                {
                    "id": "e1",
                    "url": "https://analyst.example/report",
                    "kind": "third_party_report",
                    "fetched_at": "2026-07-30",
                    "sha256": digest,
                    "excerpt_path": "wiki/raw/demo/e1.txt",
                    "paid_placement_suspected": False,
                }
            ],
            "effect_claims": [
                {
                    "claim": "Independent report measured a 7% lift over 90 days.",
                    "has_number": True,
                    "has_denominator": False,
                    "has_timeframe": True,
                    "engine": "SearchGPT",
                    "claimed_change_pp": 3.2,
                    "src": ["e1"],
                }
            ],
            "oss_health": {
                "contributors_12mo": 3,
                "commits_90d": 10,
                "last_release": "2026-07-01",
                "releases": 2,
                "tests_cover_own_logic": True,
                "license_spdx": "MIT",
                "license_absent": False,
                "commercial_restricted": False,
                "self_described_demo": False,
                "absolutist_claim_in_name": False,
                "upstream_vendor_confusable_name": False,
                "description_near_duplicate_of": [],
                "stars": 120,
                "stars_per_month": 4,
            },
            "academic_anchor": {
                "peer_reviewed": envelope(False, ["e1"]),
                "reproducible_experiments": envelope(False, ["e1"]),
                "benchmark": envelope(False, ["e1"]),
            },
            "case_studies": [],
            "unknowns": [],
        }
        self._write_profile(self._scored_profile(self.base_profile))

    def _write_excerpt(self, relative_path: str, text: str) -> str:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _write_profile(self, payload: dict) -> None:
        self.profile_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _scored_profile(self, payload: dict) -> dict:
        profile = copy.deepcopy(payload)
        evidence = {record["id"]: record for record in profile["evidence"]}
        vendor_domains = set(profile["vendor_domains"])
        noise_floors = json.loads((REPO_ROOT / "tools" / "noise_floor.json").read_text(encoding="utf-8"))
        for claim in profile["effect_claims"]:
            claim["grade_final"] = final_grade(claim, evidence, vendor_domains, noise_floors)
        profile["scores"] = calculate_scores(profile)
        profile["risk_flags"] = derive_auto_risk_flags(profile)
        return profile

    def _run(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=self.repo_root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_verify_evidence_strict_returns_zero_for_valid_profile(self):
        result = self._run(VERIFY_SCRIPT, "--strict")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)

    def test_verify_evidence_strict_returns_one_for_invalid_profile(self):
        invalid = copy.deepcopy(self.base_profile)
        invalid["effect_claims"][0]["grade_final"] = "A"
        self._write_profile(self._scored_profile(invalid))
        profile = json.loads(self.profile_path.read_text(encoding="utf-8"))
        profile["effect_claims"][0]["grade_final"] = "A"
        self._write_profile(profile)

        result = self._run(VERIFY_SCRIPT, "--strict")

        self.assertEqual(1, result.returncode)
        self.assertIn("grade_final mismatch", result.stderr)

    def test_verify_evidence_strict_does_not_mutate_profile_bytes(self):
        before = self.profile_path.read_text(encoding="utf-8")

        result = self._run(VERIFY_SCRIPT, "--strict")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, self.profile_path.read_text(encoding="utf-8"))

    def test_verify_evidence_strict_returns_one_for_unknowns_mismatch_without_mutating(self):
        broken = json.loads(self.profile_path.read_text(encoding="utf-8"))
        broken["measurement"]["samples_per_prompt"] = envelope(None, confidence="unknown")
        broken["unknowns"] = []
        self._write_profile(broken)
        before = self.profile_path.read_text(encoding="utf-8")

        result = self._run(VERIFY_SCRIPT, "--strict")

        self.assertEqual(1, result.returncode)
        self.assertIn("unknowns[] mismatch", result.stderr)
        self.assertEqual(before, self.profile_path.read_text(encoding="utf-8"))

    def test_verify_evidence_returns_two_when_products_directory_is_missing(self):
        shutil.rmtree(self.repo_root / "wiki" / "products")

        result = self._run(VERIFY_SCRIPT, "--strict")

        self.assertEqual(2, result.returncode)
        self.assertIn("missing products directory", result.stderr)

    def test_score_check_returns_zero_when_scores_are_current(self):
        before = self.profile_path.read_text(encoding="utf-8")

        result = self._run(SCORE_SCRIPT, "--check")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, self.profile_path.read_text(encoding="utf-8"))

    def test_score_check_returns_one_when_scores_are_stale_without_mutating(self):
        stale = json.loads(self.profile_path.read_text(encoding="utf-8"))
        stale["scores"]["transparency"] = 0
        stale["risk_flags"] = []
        self._write_profile(stale)
        before = self.profile_path.read_text(encoding="utf-8")

        result = self._run(SCORE_SCRIPT, "--check")

        self.assertEqual(1, result.returncode)
        self.assertIn("stale computed fields", result.stderr)
        self.assertEqual(before, self.profile_path.read_text(encoding="utf-8"))

    def test_score_rewrites_stale_computed_fields(self):
        stale = json.loads(self.profile_path.read_text(encoding="utf-8"))
        stale["effect_claims"][0]["grade_final"] = "E"
        stale["scores"]["verifiability"] = 0
        stale["risk_flags"] = []
        self._write_profile(stale)

        result = self._run(SCORE_SCRIPT)

        self.assertEqual(0, result.returncode, result.stderr)
        rewritten = json.loads(self.profile_path.read_text(encoding="utf-8"))
        self.assertEqual("B", rewritten["effect_claims"][0]["grade_final"])
        self.assertEqual(calculate_scores(rewritten), rewritten["scores"])
        self.assertEqual(derive_auto_risk_flags(rewritten), rewritten["risk_flags"])


class ToolHelpTests(unittest.TestCase):
    def test_every_executable_tool_supports_help_from_repo_root(self):
        # Break caught: direct script execution fails import/bootstrap before argparse can answer --help.
        for script_name in (
            "compile_readme.py",
            "freshness.py",
            "geo_loop.py",
            "gh_health.py",
            "score.py",
            "stage_inbox.py",
            "tavily_client.py",
            "verify_evidence.py",
        ):
            with self.subTest(script=script_name):
                result = subprocess.run(
                    [sys.executable, str(REPO_ROOT / "tools" / script_name), "--help"],
                    cwd=REPO_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("usage:", result.stdout)
                self.assertNotIn("ModuleNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
