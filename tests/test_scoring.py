import copy
import unittest

from tools.aris_geo.scoring import calculate_scores, derive_auto_risk_flags


def envelope(value, source_ids=(), confidence="stated", note=None):
    record = {"v": value, "src": list(source_ids), "conf": confidence}
    if note is not None:
        record["note"] = note
    return record


class ScoreCalculationTests(unittest.TestCase):
    def _base_profile(self):
        return {
            "schema_version": "v1",
            "slug": "demo",
            "homepage": envelope("https://vendor.example"),
            "category": ["监测/可见性追踪"],
            "evidence": [
                {
                    "id": "e-method",
                    "url": "https://vendor.example/methodology",
                    "kind": "methodology_doc",
                    "paid_placement_suspected": False,
                },
                {
                    "id": "e-registry",
                    "url": "https://registry.example/company",
                    "kind": "registry",
                    "paid_placement_suspected": False,
                },
                {
                    "id": "e-report",
                    "url": "https://analyst.example/report",
                    "kind": "third_party_report",
                    "paid_placement_suspected": False,
                },
                {
                    "id": "e-academic",
                    "url": "https://journal.example/paper",
                    "kind": "academic",
                    "paid_placement_suspected": False,
                },
            ],
            "measurement": {
                "capture_channel": envelope("browser", ["e-report"]),
                "samples_per_prompt": envelope(3, ["e-report"]),
                "reports_confidence_interval": envelope(True, ["e-report"]),
                "declares_noise_floor": envelope(True, ["e-report"]),
                "model_version_pinning": envelope(True, ["e-report"]),
                "sov_formula_public": envelope(True, ["e-report"]),
            },
            "mechanism": {
                "data_source": envelope("browser panels", ["e-report"]),
            },
            "pricing": {
                "has_public_pricing": envelope(True, ["e-report"]),
                "entry_engines": envelope(3, ["e-report"]),
                "entry_seats": envelope(3, ["e-report"]),
                "entry_prompts": envelope(500, ["e-report"]),
                "min_commit": envelope("12 months", ["e-report"]),
                "annual_only": envelope(True, ["e-report"]),
                "trial": envelope(False, ["e-report"]),
                "refund_terms": envelope(True, ["e-report"]),
                "unit_inflation_risk": envelope(False, ["e-report"]),
            },
            "entity": {
                "registry_verifiable": envelope(True, ["e-registry"]),
                "team_public": envelope(True, ["e-report"]),
            },
            "exit": {
                "data_export": envelope(False, ["e-report"]),
                "history_portable": envelope(False, ["e-report"]),
                "content_hosted_by_vendor": envelope(True, ["e-report"]),
                "contract_lock": envelope("12 months", ["e-report"]),
            },
            "effect_claims": [
                {
                    "claim": "Independent benchmark measured the lift.",
                    "has_number": True,
                    "has_denominator": False,
                    "has_timeframe": False,
                    "grade_final": "E",
                    "src": ["e-academic"],
                },
                {
                    "claim": "Vendor case study reported a 12% lift.",
                    "has_number": True,
                    "has_denominator": False,
                    "has_timeframe": False,
                    "grade_final": "A",
                    "src": ["e-method"],
                },
            ],
            "oss_health": {
                "contributors_12mo": 3,
                "commits_90d": 14,
                "last_release": "2026-07-01",
                "releases": 4,
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
                "peer_reviewed": envelope(False, ["e-academic"]),
                "reproducible_experiments": envelope(False, ["e-academic"]),
                "benchmark": envelope(False, ["e-academic"]),
            },
            "case_studies": [],
        }

    def test_calculate_scores_recomputes_all_dimensions_without_mutating_input(self):
        # Break caught: scores trust stored grades instead of recomputing deterministic outputs.
        profile = self._base_profile()
        original = copy.deepcopy(profile)

        scores = calculate_scores(profile)

        self.assertEqual(
            {
                "transparency": 5,
                "verifiability": 3,
                "lock_in_risk": 5,
                "measurement_rigor": 5,
                "oss_health": 5,
            },
            scores,
        )
        self.assertEqual(original, profile)

    def test_calculate_scores_uses_category_specific_oss_health_rules_for_agent_skills(self):
        # Break caught: zero recent commits incorrectly marks stable agent-skill repos as unhealthy.
        profile = self._base_profile()
        profile["category"] = ["agent-skill/prompt-pack"]
        profile["oss_health"].update(
            {
                "contributors_12mo": 1,
                "commits_90d": 0,
                "releases": 2,
                "tests_cover_own_logic": True,
                "license_spdx": "MIT",
                "license_absent": False,
                "commercial_restricted": False,
                "self_described_demo": False,
            }
        )

        scores = calculate_scores(profile)

        self.assertEqual(5, scores["oss_health"])


class AutoRiskFlagTests(unittest.TestCase):
    def _profile(self):
        return {
            "schema_version": "v1",
            "slug": "risky",
            "homepage": envelope("https://vendor.example", ["e-home"]),
            "category": ["监测/可见性追踪"],
            "evidence": [
                {
                    "id": "e-home",
                    "url": "https://vendor.example",
                    "kind": "vendor_doc",
                    "paid_placement_suspected": False,
                },
                {
                    "id": "e-paid-1",
                    "url": "https://media.example/top-10",
                    "kind": "third_party_report",
                    "paid_placement_suspected": True,
                },
                {
                    "id": "e-paid-2",
                    "url": "https://ugc.example/guide",
                    "kind": "third_party_report",
                    "paid_placement_suspected": True,
                },
                {
                    "id": "e-clean",
                    "url": "https://analyst.example/report",
                    "kind": "third_party_report",
                    "paid_placement_suspected": False,
                },
            ],
            "measurement": {
                "capture_channel": envelope(None, confidence="unknown"),
                "samples_per_prompt": envelope(None, confidence="unknown"),
                "reports_confidence_interval": envelope(False, ["e-home"]),
                "declares_noise_floor": envelope(False, ["e-home"]),
                "model_version_pinning": envelope(False, ["e-home"]),
                "sov_formula_public": envelope(False, ["e-home"]),
            },
            "mechanism": {
                "data_source": envelope(None, confidence="unknown"),
            },
            "pricing": {
                "has_public_pricing": envelope(False, ["e-home"]),
                "entry_engines": envelope(1, ["e-home"]),
                "entry_seats": envelope(1, ["e-home"]),
                "entry_prompts": envelope(100, ["e-home"]),
                "min_commit": envelope("12 months", ["e-home"]),
                "annual_only": envelope(True, ["e-home"]),
                "trial": envelope(False, ["e-home"]),
                "refund_terms": envelope(None, confidence="unknown"),
                "unit_inflation_risk": envelope(True, ["e-home"]),
            },
            "entity": {
                "registry_verifiable": envelope(False, ["e-home"]),
                "team_public": envelope(False, ["e-home"]),
            },
            "exit": {
                "data_export": envelope(False, ["e-home"]),
                "history_portable": envelope(False, ["e-home"]),
                "content_hosted_by_vendor": envelope(True, ["e-home"]),
                "contract_lock": envelope("12 months", ["e-home"]),
            },
            "effect_claims": [
                {
                    "claim": "SearchGPT share rose by 2 percentage points.",
                    "has_number": True,
                    "has_denominator": True,
                    "has_timeframe": True,
                    "engine": "SearchGPT",
                    "claimed_change_pp": 2.0,
                    "src": ["e-paid-1"],
                },
                {
                    "claim": "Visibility improved.",
                    "has_number": False,
                    "has_denominator": False,
                    "has_timeframe": False,
                    "src": ["e-paid-2"],
                },
                {
                    "claim": "Lifted visibility by 10%.",
                    "has_number": True,
                    "has_denominator": False,
                    "has_timeframe": False,
                    "src": ["e-clean"],
                },
            ],
            "oss_health": {
                "contributors_12mo": 1,
                "commits_90d": 0,
                "last_release": None,
                "releases": 0,
                "tests_cover_own_logic": False,
                "license_spdx": "NOASSERTION",
                "license_absent": True,
                "commercial_restricted": True,
                "self_described_demo": True,
                "absolutist_claim_in_name": True,
                "upstream_vendor_confusable_name": True,
                "description_near_duplicate_of": ["other/repo"],
                "stars": 90,
                "stars_per_month": 9,
            },
            "academic_anchor": {
                "peer_reviewed": envelope(False, ["e-home"]),
                "reproducible_experiments": envelope(False, ["e-home"]),
                "benchmark": envelope(False, ["e-home"]),
            },
            "case_studies": [
                {"brand": "Example A", "cross_verified": False, "src": ["e-home"]},
                {"brand": "Example B", "cross_verified": False, "src": ["e-home"]},
            ],
        }

    def test_derive_auto_risk_flags_emits_measurement_and_pricing_warnings(self):
        # Break caught: undisclosed measurement and pricing constraints fail to surface as deterministic labels.
        profile = self._profile()

        flags = derive_auto_risk_flags(profile)
        by_name = {flag["flag"]: flag for flag in flags}

        self.assertEqual("yellow", by_name["未披露每 prompt 采样次数"]["tier"])
        self.assertEqual("yellow", by_name["不报告置信区间或误差范围"]["tier"])
        self.assertEqual("yellow", by_name["未声明测量噪声下限"]["tier"])
        self.assertEqual("yellow", by_name["可见性份额口径未公开"]["tier"])
        self.assertEqual("orange", by_name["效果声称幅度低于该引擎测量噪声下限"]["tier"])
        self.assertEqual(["e-paid-1"], by_name["效果声称幅度低于该引擎测量噪声下限"]["src"])
        self.assertEqual("yellow", by_name["采集通道未披露"]["tier"])
        self.assertEqual("yellow", by_name["模型版本未钉定,时间序列可能断裂"]["tier"])
        self.assertEqual("yellow", by_name["数据来源未披露"]["tier"])
        self.assertEqual("yellow", by_name["无公开定价 / 仅年付 / 无试用 / 退款条款未公开"]["tier"])
        self.assertEqual("yellow", by_name["入门档仅覆盖单一引擎 / 仅 1 个席位"]["tier"])
        self.assertEqual("orange", by_name["计价单位随监测范围膨胀"]["tier"])
        self.assertEqual("orange", by_name["无数据导出 / 最低合约期 > 6 个月"]["tier"])

    def test_derive_auto_risk_flags_emits_evidence_and_oss_concerns(self):
        # Break caught: low-verifiability and OSS hygiene signals are omitted from automatic labels.
        profile = self._profile()

        flags = derive_auto_risk_flags(profile)
        by_name = {flag["flag"]: flag for flag in flags}

        self.assertEqual("yellow", by_name["团队信息未公开 / 客户案例未能交叉验证"]["tier"])
        self.assertEqual("orange", by_name["效果声称以 D/E 级为主"]["tier"])
        self.assertEqual("orange", by_name["第三方证据主要来自疑似投放内容"]["tier"])
        self.assertEqual("yellow", by_name["无 license 或 NOASSERTION"]["tier"])
        self.assertEqual("yellow", by_name["license 含商用限制"]["tier"])
        self.assertEqual("yellow", by_name["停更(按 category 判定)"]["tier"])
        self.assertEqual("yellow", by_name["贡献者集中于单人"]["tier"])
        self.assertEqual("yellow", by_name["无覆盖自身逻辑的测试"]["tier"])
        self.assertEqual("yellow", by_name["自述为 Demo"]["tier"])
        self.assertEqual("yellow", by_name["仓库名含绝对化宣称"]["tier"])
        self.assertEqual("yellow", by_name["命名易与上游模型厂商混淆"]["tier"])
        self.assertEqual("yellow", by_name["描述与其他仓库高度相似"]["tier"])

    def test_derive_auto_risk_flags_does_not_mark_unknown_engine_d_claim_as_noise_floor(self):
        # Break caught: any numeric D-grade claim is mislabeled as a noise-floor downgrade.
        profile = self._profile()
        profile["effect_claims"] = [
            {
                "claim": "Vendor page claimed a 1 point lift.",
                "has_number": True,
                "has_denominator": False,
                "has_timeframe": False,
                "engine": "UnknownEngine",
                "claimed_change_pp": 1.0,
                "src": ["e-home"],
            }
        ]

        flags = derive_auto_risk_flags(profile)
        flag_names = {flag["flag"] for flag in flags}

        self.assertNotIn("效果声称幅度低于该引擎测量噪声下限", flag_names)

    def test_derive_auto_risk_flags_emits_claim_level_flag_for_vendor_hosted_ab_downgrades(self):
        # Break caught: vendor-hosted A/B candidates lose grade strength without an explicit deterministic label.
        profile = self._profile()
        profile["evidence"].append(
            {
                "id": "e-method-vendor",
                "url": "https://vendor.example/methodology",
                "kind": "methodology_doc",
                "paid_placement_suspected": False,
            }
        )
        profile["evidence"].append(
            {
                "id": "e-dataset",
                "url": "https://vendor.example/dataset",
                "kind": "third_party_dataset",
                "paid_placement_suspected": False,
            }
        )
        profile["effect_claims"] = [
            {
                "claim": "Vendor-hosted methodology and dataset reported the lift.",
                "has_number": True,
                "has_denominator": True,
                "has_timeframe": True,
                "src": ["e-method-vendor", "e-dataset"],
            }
        ]

        flags = derive_auto_risk_flags(profile)
        by_name = {flag["flag"]: flag for flag in flags}

        self.assertEqual("orange", by_name["A/B 候选声称仅由供应商域名来源支撑"]["tier"])
        self.assertEqual(["e-method-vendor", "e-dataset"], by_name["A/B 候选声称仅由供应商域名来源支撑"]["src"])

    def test_derive_auto_risk_flags_emits_claim_level_flag_for_suspected_paid_placement_downgrades(self):
        # Break caught: suspected-placement downgrades are silent even when every relevant report is flagged.
        profile = self._profile()
        profile["effect_claims"] = [
            {
                "claim": "Third-party review measured the lift.",
                "has_number": True,
                "has_denominator": True,
                "has_timeframe": True,
                "src": ["e-paid-1"],
            }
        ]

        flags = derive_auto_risk_flags(profile)
        by_name = {flag["flag"]: flag for flag in flags}

        self.assertEqual(
            "orange",
            by_name["A/B 候选声称的第三方报告来源均标记为疑似投放内容"]["tier"],
        )
        self.assertEqual(
            ["e-paid-1"],
            by_name["A/B 候选声称的第三方报告来源均标记为疑似投放内容"]["src"],
        )

    def test_derive_auto_risk_flags_emits_poisoning_fingerprint_label_at_three_distinct_hits(self):
        # Break caught: poisoning fingerprints do not trigger the auto label at the documented threshold.
        profile = self._profile()
        profile["tactics"] = {
            "poisoning_fingerprints": ["批量内容生成", "平台铺量", "榜单伪装", "批量内容生成", ""]
        }

        flags = derive_auto_risk_flags(profile)
        by_name = {flag["flag"]: flag for flag in flags}

        self.assertEqual("orange", by_name["投毒指纹命中 ≥3 项"]["tier"])


if __name__ == "__main__":
    unittest.main()
