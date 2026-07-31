import copy
import unittest

from tools.aris_geo.grading import final_grade


class FinalGradeTests(unittest.TestCase):
    def setUp(self):
        self.vendor_domains = {"vendor.example"}
        self.noise_floors = {
            "engines": {
                "SearchGPT": {"attribution_floor_pp": 3.0},
                "Gemini": {"attribution_floor_pp": 1.5},
            }
        }

    def _evidence(self, evidence_id, *, url, kind, paid_placement_suspected=False):
        return {
            "id": evidence_id,
            "url": url,
            "kind": kind,
            "paid_placement_suspected": paid_placement_suspected,
        }

    def test_final_grade_assigns_a_and_b_from_independent_evidence(self):
        # Break caught: independent academic and third-party evidence collapse to first-party grades.
        evidence = {
            "academic": self._evidence(
                "academic",
                url="https://journal.example/paper",
                kind="academic",
            ),
            "report": self._evidence(
                "report",
                url="https://analyst.example/report",
                kind="third_party_report",
            ),
        }

        academic_claim = {
            "claim": "Academic benchmark recorded a lift.",
            "has_number": True,
            "has_denominator": False,
            "has_timeframe": False,
            "src": ["academic"],
        }
        report_claim = {
            "claim": "Third-party report measured the lift.",
            "has_number": True,
            "has_denominator": False,
            "has_timeframe": False,
            "src": ["report"],
        }

        self.assertEqual(
            "A",
            final_grade(academic_claim, evidence, self.vendor_domains, self.noise_floors),
        )
        self.assertEqual(
            "B",
            final_grade(report_claim, evidence, self.vendor_domains, self.noise_floors),
        )

    def test_final_grade_falls_back_to_claim_structure_for_c_d_and_e(self):
        # Break caught: first-party claims ignore denominator/timeframe mechanics.
        evidence = {
            "vendor": self._evidence(
                "vendor",
                url="https://vendor.example/case-study",
                kind="vendor_marketing",
            )
        }
        cases = [
            (
                {
                    "claim": "Lifted share of voice by 12% over 90 days.",
                    "has_number": True,
                    "has_denominator": False,
                    "has_timeframe": True,
                    "src": ["vendor"],
                },
                "C",
            ),
            (
                {
                    "claim": "Lifted visibility by 12%.",
                    "has_number": True,
                    "has_denominator": False,
                    "has_timeframe": False,
                    "src": ["vendor"],
                },
                "D",
            ),
            (
                {
                    "claim": "Improved visibility.",
                    "has_number": False,
                    "has_denominator": False,
                    "has_timeframe": False,
                    "src": ["vendor"],
                },
                "E",
            ),
            (
                {
                    "claim": "Unattributed lift.",
                    "has_number": True,
                    "has_denominator": True,
                    "has_timeframe": True,
                    "src": [],
                },
                "E",
            ),
        ]

        for claim, expected in cases:
            with self.subTest(expected=expected, claim=claim["claim"]):
                self.assertEqual(
                    expected,
                    final_grade(claim, evidence, self.vendor_domains, self.noise_floors),
                )

    def test_final_grade_downgrades_ab_claims_when_all_sources_are_vendor_hosted(self):
        # Break caught: vendor-hosted A/B evidence retains an independent grade.
        evidence = {
            "method": self._evidence(
                "method",
                url="https://vendor.example/methodology",
                kind="methodology_doc",
            ),
            "dataset": self._evidence(
                "dataset",
                url="https://vendor.example/dataset",
                kind="third_party_dataset",
            ),
            "report": self._evidence(
                "report",
                url="https://vendor.example/report",
                kind="third_party_report",
            ),
        }

        methodology_claim = {
            "claim": "Methodology-backed lift over 90 days.",
            "has_number": True,
            "has_denominator": False,
            "has_timeframe": True,
            "src": ["method", "dataset"],
        }
        report_claim = {
            "claim": "Third-party hosted on the vendor site measured the lift.",
            "has_number": True,
            "has_denominator": False,
            "has_timeframe": True,
            "src": ["report"],
        }

        self.assertEqual(
            "C",
            final_grade(methodology_claim, evidence, self.vendor_domains, self.noise_floors),
        )
        self.assertEqual(
            "C",
            final_grade(report_claim, evidence, self.vendor_domains, self.noise_floors),
        )

    def test_final_grade_downgrades_b_claims_when_all_reports_are_suspected_paid_placements(self):
        # Break caught: suspected paid placements still count as clean third-party validation.
        evidence = {
            "report": self._evidence(
                "report",
                url="https://media.example/review",
                kind="third_party_report",
                paid_placement_suspected=True,
            )
        }
        claim = {
            "claim": "Media review measured the lift over 90 days.",
            "has_number": True,
            "has_denominator": False,
            "has_timeframe": True,
            "src": ["report"],
        }

        self.assertEqual(
            "C",
            final_grade(claim, evidence, self.vendor_domains, self.noise_floors),
        )

    def test_final_grade_downgrades_claims_below_a_known_noise_floor(self):
        # Break caught: percentage-point claims below the engine floor still keep elevated grades.
        evidence = {
            "report": self._evidence(
                "report",
                url="https://analyst.example/report",
                kind="third_party_report",
            )
        }
        claim = {
            "claim": "SearchGPT share rose by 2.5 percentage points.",
            "has_number": True,
            "has_denominator": True,
            "has_timeframe": True,
            "engine": "SearchGPT",
            "claimed_change_pp": 2.5,
            "src": ["report"],
        }

        self.assertEqual(
            "D",
            final_grade(claim, evidence, self.vendor_domains, self.noise_floors),
        )

    def test_final_grade_keeps_grade_when_claimed_change_meets_floor_exceeds_floor_or_is_absent(self):
        # Break caught: the noise-floor downgrade triggers at the threshold, above it, or without a numeric field.
        evidence = {
            "report": self._evidence(
                "report",
                url="https://analyst.example/report",
                kind="third_party_report",
            )
        }
        cases = [
            ({"claimed_change_pp": 3.0, "engine": "SearchGPT"}, "B"),
            ({"claimed_change_pp": 3.2, "engine": "SearchGPT"}, "B"),
            ({}, "B"),
            ({"claimed_change_pp": 1.0, "engine": "UnknownEngine"}, "B"),
        ]

        for extras, expected in cases:
            claim = {
                "claim": "Third-party report measured the lift.",
                "has_number": True,
                "has_denominator": False,
                "has_timeframe": False,
                "src": ["report"],
            }
            claim.update(extras)
            with self.subTest(extras=extras):
                self.assertEqual(
                    expected,
                    final_grade(claim, evidence, self.vendor_domains, self.noise_floors),
                )

    def test_final_grade_rejects_invalid_claimed_change_pp_values(self):
        # Break caught: bools and non-numeric values silently participate in noise-floor comparisons.
        evidence = {
            "report": self._evidence(
                "report",
                url="https://analyst.example/report",
                kind="third_party_report",
            )
        }
        base_claim = {
            "claim": "Third-party report measured the lift.",
            "has_number": True,
            "has_denominator": False,
            "has_timeframe": False,
            "engine": "SearchGPT",
            "src": ["report"],
        }

        for bad_value in (True, "3.0", object()):
            claim = copy.deepcopy(base_claim)
            claim["claimed_change_pp"] = bad_value
            with self.subTest(bad_value=bad_value):
                with self.assertRaises((TypeError, ValueError)):
                    final_grade(claim, evidence, self.vendor_domains, self.noise_floors)


if __name__ == "__main__":
    unittest.main()
