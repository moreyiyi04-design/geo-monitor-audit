from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.build_publication import validate_committed_shortlist
from tools.aris_geo.shortlist import validate_shortlist


def valid_entry(
    slug: str = "timus_geo",
    *,
    kind: str = "commercial",
    status: str = "selected_poc",
) -> dict:
    return {
        "slug": slug,
        "name": "透镜GEO",
        "kind": kind,
        "status": status,
        "scenarios": ["domestic_audit", "regulated"],
        "solves": "保存真实交互证据",
        "why_selected": ["中立账号", "完整录屏"],
        "evidence_basis": [f"wiki/products/{slug}.json#e1"],
        "limitations": ["逐端矩阵未公开"],
        "replacement_gap": "现有候选中少有完整录屏",
        "professional_assessment": "原始交互证据突出，适合品牌审计。",
        "enterprise_assessment": "API等企业能力尚未公开。",
    }


def valid_payload() -> dict:
    return {
        "schema_version": "v1",
        "max_unique": 8,
        "entries": [valid_entry()],
    }


class ShortlistValidationTests(unittest.TestCase):
    def test_accepts_complete_commercial_entry(self):
        self.assertEqual([], validate_shortlist(valid_payload(), {"timus_geo"}))

    def test_rejects_duplicate_and_unknown_profile_slugs(self):
        payload = valid_payload()
        payload["entries"].append(copy.deepcopy(payload["entries"][0]))

        errors = validate_shortlist(payload, {"another_profile"})

        self.assertIn("duplicate slug: timus_geo", errors)
        self.assertIn("unknown profile slug: timus_geo", errors)

    def test_rejects_more_than_eight_unique_entries(self):
        payload = valid_payload()
        payload["max_unique"] = 9
        payload["entries"] = [
            valid_entry(f"product_{index}")
            for index in range(9)
        ]

        errors = validate_shortlist(
            payload,
            {f"product_{index}" for index in range(9)},
        )

        self.assertIn("max_unique must be between 1 and 8", errors)
        self.assertIn("shortlist has 9 unique entries; maximum is 8", errors)

    def test_rejects_invalid_kind_status_and_research_recommendation(self):
        payload = valid_payload()
        payload["entries"] = [
            valid_entry("bad_kind", kind="service", status="selected_poc"),
            valid_entry("bad_status", status="winner"),
            valid_entry("paper", kind="research", status="selected_poc"),
        ]

        errors = validate_shortlist(payload, {"bad_kind", "bad_status", "paper"})

        self.assertIn("bad_kind: invalid kind: service", errors)
        self.assertIn("bad_status: invalid status: winner", errors)
        self.assertIn("paper: research entries cannot be selected_poc", errors)

    def test_rejects_missing_decision_fields(self):
        payload = valid_payload()
        entry = payload["entries"][0]
        entry["scenarios"] = []
        entry["solves"] = ""
        entry["why_selected"] = []
        entry["evidence_basis"] = []
        entry["limitations"] = []
        entry["replacement_gap"] = ""

        errors = validate_shortlist(payload, {"timus_geo"})

        for field in (
            "scenarios",
            "solves",
            "why_selected",
            "evidence_basis",
            "limitations",
            "replacement_gap",
        ):
            self.assertIn(f"timus_geo: {field} must be non-empty", errors)

    def test_rejects_missing_professional_and_enterprise_assessments(self):
        payload = valid_payload()
        entry = payload["entries"][0]
        del entry["professional_assessment"]
        del entry["enterprise_assessment"]

        errors = validate_shortlist(payload, {"timus_geo"})

        self.assertIn(
            "timus_geo: professional_assessment must be non-empty",
            errors,
        )
        self.assertIn(
            "timus_geo: enterprise_assessment must be non-empty",
            errors,
        )

    def test_rejects_selected_open_source_without_all_production_gates(self):
        payload = valid_payload()
        entry = valid_entry("aperture", kind="open-source", status="selected_poc")
        entry["open_source_gates"] = {
            "runnable_code": True,
            "license": True,
            "raw_results": True,
            "reproducible_setup": True,
            "tests_or_benchmark": False,
        }
        payload["entries"] = [entry]

        errors = validate_shortlist(payload, {"aperture"})

        self.assertIn(
            "aperture: selected open-source entry failed gate: tests_or_benchmark",
            errors,
        )

    def test_accepts_open_source_watch_entry_with_explicit_failed_gates(self):
        payload = valid_payload()
        entry = valid_entry("aperture", kind="open-source", status="watch")
        entry["open_source_gates"] = {
            "runnable_code": True,
            "license": True,
            "raw_results": True,
            "reproducible_setup": True,
            "tests_or_benchmark": False,
        }
        payload["entries"] = [entry]

        self.assertEqual([], validate_shortlist(payload, {"aperture"}))


class ShortlistBuildGateTests(unittest.TestCase):
    def test_build_gate_rejects_shortlist_slug_without_profile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            products_dir = repo_root / "wiki" / "products"
            products_dir.mkdir(parents=True)
            (products_dir / "timus_geo.json").write_text("{}", encoding="utf-8")
            shortlist_path = repo_root / "wiki" / "shortlist.json"
            payload = valid_payload()
            payload["entries"][0]["slug"] = "missing_product"
            shortlist_path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "unknown profile slug: missing_product"):
                validate_committed_shortlist(repo_root, shortlist_path)


if __name__ == "__main__":
    unittest.main()
