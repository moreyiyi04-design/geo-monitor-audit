import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.aris_geo.evidence import sha256_file, validate_profile
from tools.aris_geo.schema import iter_envelopes


class EvidenceValidationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="aris-geo-evidence-"))
        self.addCleanup(lambda: shutil.rmtree(self.tempdir))
        self.repo_root = self.tempdir / "repo"
        self.repo_root.mkdir()

    def _write_excerpt(self, relative_path, text):
        excerpt_path = self.repo_root / relative_path
        excerpt_path.parent.mkdir(parents=True, exist_ok=True)
        excerpt_path.write_text(text, encoding="utf-8")
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _make_profile(self):
        digest = self._write_excerpt("wiki/raw/demo/e1.txt", "Pricing page excerpt")
        return {
            "schema_version": "v1",
            "evidence": [
                {
                    "id": "e1",
                    "url": "https://vendor.example/pricing",
                    "kind": "vendor_pricing_page",
                    "fetched_at": "2026-07-30",
                    "sha256": digest,
                    "excerpt_path": "wiki/raw/demo/e1.txt",
                    "paid_placement_suspected": False,
                }
            ],
            "name_cn": {"v": "演示产品", "src": ["e1"], "conf": "stated"},
            "measurement": {
                "samples_per_prompt": {"v": None, "src": [], "conf": "unknown"}
            },
            "scores": {"transparency": 5},
            "risk_flags": [{"flag": "computed"}],
            "audit": {"rounds": 1},
            "oss_health": {"stars": 99},
            "unknowns": ["measurement.samples_per_prompt"],
        }

    def test_iter_envelopes_discovers_leaf_envelopes_and_skips_computed_subtrees(self):
        # Break caught: descending into scores/risk_flags/audit/oss_health or missing real envelopes.
        profile = self._make_profile()

        envelopes = list(iter_envelopes(profile))

        self.assertEqual(
            ["name_cn", "measurement.samples_per_prompt"],
            [envelope.path for envelope in envelopes],
        )
        self.assertEqual("演示产品", envelopes[0].value)
        self.assertIsNone(envelopes[1].value)

    def test_validate_profile_accepts_valid_profile_and_resolves_sources(self):
        # Break caught: valid evidence ids do not resolve into the validation report.
        profile = self._make_profile()

        report = validate_profile(profile, self.repo_root)

        self.assertTrue(report.ok)
        self.assertEqual([], report.errors)
        self.assertIn("e1", report.evidence_by_id)
        self.assertEqual(
            ("e1",),
            report.envelopes_by_path["name_cn"].source_ids,
        )
        self.assertEqual(
            self._write_excerpt("wiki/raw/demo/copy.txt", "Pricing page excerpt"),
            sha256_file(self.repo_root / "wiki/raw/demo/e1.txt"),
        )

    def test_validate_profile_requires_note_for_inferred_envelopes(self):
        # Break caught: inferred envelopes can omit the reasoning note.
        profile = self._make_profile()
        profile["name_cn"] = {"v": "演示产品", "src": ["e1"], "conf": "inferred"}

        report = validate_profile(profile, self.repo_root)

        self.assertFalse(report.ok)
        self.assertIn("name_cn: inferred envelopes require a non-empty note", report.errors)

    def test_validate_profile_requires_unknowns_to_match_unknown_envelopes(self):
        # Break caught: unknown envelopes can be hidden by omitting them from unknowns[].
        profile = self._make_profile()
        profile["unknowns"] = []

        report = validate_profile(profile, self.repo_root)

        self.assertFalse(report.ok)
        self.assertIn(
            "unknowns[] mismatch: missing measurement.samples_per_prompt",
            report.errors,
        )

    def test_validate_profile_detects_hash_mismatch(self):
        # Break caught: excerpt bytes change without the recorded sha256 changing.
        profile = self._make_profile()
        profile["evidence"][0]["sha256"] = "0" * 64

        report = validate_profile(profile, self.repo_root)

        self.assertFalse(report.ok)
        self.assertIn(
            "evidence e1: sha256 mismatch for wiki/raw/demo/e1.txt",
            report.errors,
        )

    def test_validate_profile_requires_paid_placement_flag(self):
        # Break caught: evidence records can omit the paid-placement signal entirely.
        profile = self._make_profile()
        del profile["evidence"][0]["paid_placement_suspected"]

        report = validate_profile(profile, self.repo_root)

        self.assertFalse(report.ok)
        self.assertIn(
            "evidence e1: paid_placement_suspected must be a bool",
            report.errors,
        )

    def test_validate_profile_requires_boolean_paid_placement_flag(self):
        # Break caught: evidence records accept truthy non-bool values for paid placement.
        profile = self._make_profile()
        profile["evidence"][0]["paid_placement_suspected"] = "false"

        report = validate_profile(profile, self.repo_root)

        self.assertFalse(report.ok)
        self.assertIn(
            "evidence e1: paid_placement_suspected must be a bool",
            report.errors,
        )

    def test_validate_profile_rejects_duplicate_evidence_ids(self):
        # Break caught: duplicate evidence ids silently overwrite earlier records.
        profile = self._make_profile()
        profile["evidence"].append(
            {
                "id": "e1",
                "url": "https://vendor.example/duplicate",
                "kind": "vendor_doc",
                "fetched_at": "2026-07-30",
                "sha256": self._write_excerpt("wiki/raw/demo/e1b.txt", "Duplicate excerpt"),
                "excerpt_path": "wiki/raw/demo/e1b.txt",
                "paid_placement_suspected": False,
            }
        )

        report = validate_profile(profile, self.repo_root)

        self.assertFalse(report.ok)
        self.assertIn("evidence e1: duplicate id", report.errors)

    def test_validate_profile_rejects_non_hex_sha256(self):
        # Break caught: non-hex sha256 values pass as long as they have length 64.
        profile = self._make_profile()
        profile["evidence"][0]["sha256"] = "g" * 64

        report = validate_profile(profile, self.repo_root)

        self.assertFalse(report.ok)
        self.assertIn(
            "evidence e1: sha256 must be 64 hexadecimal characters",
            report.errors,
        )

    def test_validate_profile_rejects_excerpt_paths_outside_repo_root(self):
        # Break caught: evidence excerpts can escape the repository root via relative paths.
        profile = self._make_profile()
        profile["evidence"][0]["excerpt_path"] = "../escape.txt"

        report = validate_profile(profile, self.repo_root)

        self.assertFalse(report.ok)
        self.assertIn(
            "evidence e1: excerpt_path escapes repository root",
            report.errors,
        )


if __name__ == "__main__":
    unittest.main()
