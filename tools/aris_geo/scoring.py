from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .grading import GRADE_WEIGHTS, assess_claim, final_grade


def calculate_scores(profile: dict[str, Any]) -> dict[str, int]:
    evidence = _evidence_by_id(profile)
    vendor_domains = _vendor_domains(profile)
    noise_floors = _load_noise_floors()

    return {
        "transparency": _transparency_score(profile),
        "verifiability": _verifiability_score(profile, evidence, vendor_domains, noise_floors),
        "lock_in_risk": _lock_in_score(profile),
        "measurement_rigor": _measurement_rigor_score(profile),
        "oss_health": _oss_health_score(profile),
    }


def derive_auto_risk_flags(profile: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = _evidence_by_id(profile)
    vendor_domains = _vendor_domains(profile)
    noise_floors = _load_noise_floors()
    scores = calculate_scores(profile)

    flags: list[dict[str, Any]] = []
    index: dict[str, dict[str, Any]] = {}

    def add_flag(flag: str, tier: str, source_ids: list[str] | tuple[str, ...] = ()) -> None:
        if flag not in index:
            record = {"flag": flag, "tier": tier, "origin": "auto", "src": []}
            index[flag] = record
            flags.append(record)
        for source_id in source_ids:
            if source_id not in index[flag]["src"]:
                index[flag]["src"].append(source_id)

    measurement = profile.get("measurement") or {}
    mechanism = profile.get("mechanism") or {}
    pricing = profile.get("pricing") or {}
    entity = profile.get("entity") or {}
    exit_data = profile.get("exit") or {}
    oss_health = profile.get("oss_health") or {}

    samples = measurement.get("samples_per_prompt")
    if _is_unknown(samples):
        add_flag("未披露每 prompt 采样次数", "yellow", _source_ids(samples))
    if not _is_true(measurement.get("reports_confidence_interval")):
        add_flag("不报告置信区间或误差范围", "yellow", _source_ids(measurement.get("reports_confidence_interval")))
    if not _is_true(measurement.get("declares_noise_floor")):
        add_flag("未声明测量噪声下限", "yellow", _source_ids(measurement.get("declares_noise_floor")))
    if not _is_true(measurement.get("sov_formula_public")):
        add_flag("可见性份额口径未公开", "yellow", _source_ids(measurement.get("sov_formula_public")))
    if _is_unknown(measurement.get("capture_channel")) or _value(measurement.get("capture_channel")) == "undisclosed":
        add_flag("采集通道未披露", "yellow", _source_ids(measurement.get("capture_channel")))
    if not _is_true(measurement.get("model_version_pinning")):
        add_flag("模型版本未钉定,时间序列可能断裂", "yellow", _source_ids(measurement.get("model_version_pinning")))
    if _is_unknown(mechanism.get("data_source")) or _value(mechanism.get("data_source")) == "undisclosed":
        add_flag("数据来源未披露", "yellow", _source_ids(mechanism.get("data_source")))

    below_floor_sources: list[str] = []
    vendor_hosted_downgrade_sources: list[str] = []
    suspected_paid_sources: list[str] = []
    claim_assessments = []
    for claim in profile.get("effect_claims") or []:
        claimed_change_pp = claim.get("claimed_change_pp")
        if "claimed_change_pp" in claim and (isinstance(claimed_change_pp, bool) or not isinstance(claimed_change_pp, (int, float))):
            raise TypeError("claimed_change_pp must be an int or float when present")
        assessment = assess_claim(claim, evidence, vendor_domains, noise_floors)
        claim_assessments.append((claim, assessment))
        if "below_noise_floor" in assessment.downgrade_reasons:
            below_floor_sources.extend(_claim_source_ids(claim))
        if "vendor_hosted" in assessment.downgrade_reasons:
            vendor_hosted_downgrade_sources.extend(_claim_source_ids(claim))
        if "suspected_paid_placement" in assessment.downgrade_reasons:
            suspected_paid_sources.extend(_claim_source_ids(claim))
    if below_floor_sources:
        add_flag("效果声称幅度低于该引擎测量噪声下限", "orange", below_floor_sources)
    if vendor_hosted_downgrade_sources:
        add_flag("A/B 候选声称仅由供应商域名来源支撑", "orange", vendor_hosted_downgrade_sources)
    if suspected_paid_sources:
        add_flag("A/B 候选声称的第三方报告来源均标记为疑似投放内容", "orange", suspected_paid_sources)

    pricing_flag_sources = []
    if not _is_true(pricing.get("has_public_pricing")):
        pricing_flag_sources.extend(_source_ids(pricing.get("has_public_pricing")))
    if _is_true(pricing.get("annual_only")):
        pricing_flag_sources.extend(_source_ids(pricing.get("annual_only")))
    if _value(pricing.get("trial")) is False or _is_unknown(pricing.get("trial")):
        pricing_flag_sources.extend(_source_ids(pricing.get("trial")))
    if not _disclosed(pricing.get("refund_terms")):
        pricing_flag_sources.extend(_source_ids(pricing.get("refund_terms")))
    if pricing_flag_sources:
        add_flag("无公开定价 / 仅年付 / 无试用 / 退款条款未公开", "yellow", pricing_flag_sources)

    if _numeric_value(pricing.get("entry_engines"), default=0) <= 1 or _numeric_value(pricing.get("entry_seats"), default=0) <= 1:
        add_flag(
            "入门档仅覆盖单一引擎 / 仅 1 个席位",
            "yellow",
            _source_ids(pricing.get("entry_engines")) + _source_ids(pricing.get("entry_seats")),
        )

    if _is_true(pricing.get("unit_inflation_risk")):
        add_flag("计价单位随监测范围膨胀", "orange", _source_ids(pricing.get("unit_inflation_risk")))

    if _value(exit_data.get("data_export")) is False or _months_value(pricing.get("min_commit")) > 6:
        add_flag(
            "无数据导出 / 最低合约期 > 6 个月",
            "orange",
            _source_ids(exit_data.get("data_export")) + _source_ids(pricing.get("min_commit")),
        )

    case_studies = profile.get("case_studies") or []
    unverified_case_sources = []
    for study in case_studies:
        if not study.get("cross_verified", False):
            unverified_case_sources.extend(_claim_source_ids(study))
    if not _is_true(entity.get("team_public")) or unverified_case_sources:
        add_flag(
            "团队信息未公开 / 客户案例未能交叉验证",
            "yellow",
            _source_ids(entity.get("team_public")) + unverified_case_sources,
        )

    degraded_sources: list[str] = []
    degraded_count = 0
    claims = profile.get("effect_claims") or []
    for claim, assessment in claim_assessments:
        if assessment.final_grade in {"D", "E"}:
            degraded_count += 1
            degraded_sources.extend(_claim_source_ids(claim))
    if claims and (scores["verifiability"] < 2 or degraded_count / len(claims) > 0.5):
        add_flag("效果声称以 D/E 级为主", "orange", degraded_sources)

    report_evidence = [record for record in profile.get("evidence") or [] if record.get("kind") == "third_party_report"]
    suspected_reports = [record for record in report_evidence if bool(record.get("paid_placement_suspected"))]
    if report_evidence and len(suspected_reports) / len(report_evidence) > 0.5:
        add_flag("第三方证据主要来自疑似投放内容", "orange", [record["id"] for record in suspected_reports if "id" in record])

    fingerprints = _distinct_nonempty_strings((profile.get("tactics") or {}).get("poisoning_fingerprints"))
    if len(fingerprints) >= 3:
        add_flag("投毒指纹命中 ≥3 项", "orange")

    if bool(oss_health.get("license_absent")) or oss_health.get("license_spdx") == "NOASSERTION":
        add_flag("无 license 或 NOASSERTION", "yellow")
    if bool(oss_health.get("commercial_restricted")):
        add_flag("license 含商用限制", "yellow")
    if _is_stale(profile):
        add_flag("停更(按 category 判定)", "yellow")
    if int(oss_health.get("contributors_12mo") or 0) <= 1:
        add_flag("贡献者集中于单人", "yellow")
    if not bool(oss_health.get("tests_cover_own_logic")):
        add_flag("无覆盖自身逻辑的测试", "yellow")
    if bool(oss_health.get("self_described_demo")):
        add_flag("自述为 Demo", "yellow")
    if bool(oss_health.get("absolutist_claim_in_name")):
        add_flag("仓库名含绝对化宣称", "yellow")
    if bool(oss_health.get("upstream_vendor_confusable_name")):
        add_flag("命名易与上游模型厂商混淆", "yellow")
    if oss_health.get("description_near_duplicate_of"):
        add_flag("描述与其他仓库高度相似", "yellow")

    return flags


def _transparency_score(profile: dict[str, Any]) -> int:
    evidence = profile.get("evidence") or []
    mechanism = profile.get("mechanism") or {}
    pricing = profile.get("pricing") or {}
    entity = profile.get("entity") or {}

    points = 0
    points += int(_is_true(pricing.get("has_public_pricing")))
    points += int(any(record.get("kind") == "methodology_doc" for record in evidence))
    points += int(_is_true(entity.get("registry_verifiable")))
    points += int(_disclosed(mechanism.get("data_source")))
    points += int(_disclosed(pricing.get("refund_terms")))
    return points


def _verifiability_score(
    profile: dict[str, Any],
    evidence: dict[str, dict[str, Any]],
    vendor_domains: set[str],
    noise_floors: dict[str, Any],
) -> int:
    claims = profile.get("effect_claims") or []
    if not claims:
        return 0
    weights = [
        GRADE_WEIGHTS[final_grade(claim, evidence, vendor_domains, noise_floors)]
        for claim in claims
    ]
    return int(round(5 * sum(weights) / len(weights)))


def _lock_in_score(profile: dict[str, Any]) -> int:
    pricing = profile.get("pricing") or {}
    exit_data = profile.get("exit") or {}

    points = 0
    points += int(_value(exit_data.get("data_export")) is False)
    points += int(_is_true(exit_data.get("content_hosted_by_vendor")))
    points += int(_months_value(pricing.get("min_commit")) > 6)
    points += int(_is_true(pricing.get("annual_only")))
    points += int(_value(exit_data.get("history_portable")) is False)
    return points


def _measurement_rigor_score(profile: dict[str, Any]) -> int:
    measurement = profile.get("measurement") or {}

    points = 0
    points += int(_value(measurement.get("capture_channel")) == "browser")
    points += int(_numeric_value(measurement.get("samples_per_prompt"), default=0) > 1 and not _is_unknown(measurement.get("samples_per_prompt")))
    points += int(_is_true(measurement.get("reports_confidence_interval")))
    points += int(_is_true(measurement.get("declares_noise_floor")))
    points += int(_is_true(measurement.get("sov_formula_public")))
    return points


def _oss_health_score(profile: dict[str, Any]) -> int:
    oss_health = profile.get("oss_health") or {}
    categories = set(profile.get("category") or [])
    license_good = not bool(oss_health.get("license_absent")) and oss_health.get("license_spdx") != "NOASSERTION"
    release_present = bool(oss_health.get("releases")) or bool(oss_health.get("last_release"))

    if "agent-skill/prompt-pack" in categories:
        checks = [
            license_good,
            not bool(oss_health.get("commercial_restricted")),
            release_present,
            bool(oss_health.get("tests_cover_own_logic")),
            not bool(oss_health.get("self_described_demo")),
        ]
    elif "学术参考实现" in categories:
        academic = profile.get("academic_anchor") or {}
        checks = [
            _is_true(academic.get("peer_reviewed")),
            _is_true(academic.get("reproducible_experiments")),
            _is_true(academic.get("benchmark")),
            license_good,
            not bool(oss_health.get("self_described_demo")),
        ]
    elif "资源清单" in categories:
        checks = [
            license_good,
            int(oss_health.get("commits_90d") or 0) > 0,
            release_present,
            int(oss_health.get("contributors_12mo") or 0) > 0,
            not bool(oss_health.get("self_described_demo")),
        ]
    else:
        checks = [
            license_good,
            int(oss_health.get("contributors_12mo") or 0) > 1,
            int(oss_health.get("commits_90d") or 0) > 0,
            release_present,
            bool(oss_health.get("tests_cover_own_logic")),
        ]
    return sum(int(check) for check in checks)


def _is_stale(profile: dict[str, Any]) -> bool:
    categories = set(profile.get("category") or [])
    oss_health = profile.get("oss_health") or {}
    commits_90d = int(oss_health.get("commits_90d") or 0)
    release_present = bool(oss_health.get("releases")) or bool(oss_health.get("last_release"))

    if "agent-skill/prompt-pack" in categories:
        return commits_90d == 0 and not release_present and not bool(oss_health.get("tests_cover_own_logic"))
    if "学术参考实现" in categories:
        academic = profile.get("academic_anchor") or {}
        anchored = any(
            _is_true(academic.get(field))
            for field in ("peer_reviewed", "reproducible_experiments", "benchmark")
        )
        return not anchored and commits_90d == 0 and not release_present
    if "资源清单" in categories:
        return commits_90d == 0
    return commits_90d == 0


def _evidence_by_id(profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        record["id"]: record
        for record in profile.get("evidence") or []
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }


def _vendor_domains(profile: dict[str, Any]) -> set[str]:
    domains = set()
    for domain in profile.get("vendor_domains") or []:
        normalized = _normalize_domain(domain)
        if normalized:
            domains.add(normalized)
    homepage = _value(profile.get("homepage"))
    if isinstance(homepage, str):
        normalized = _normalize_domain(urlparse(homepage).netloc or homepage)
        if normalized:
            domains.add(normalized)
    return domains


def _load_noise_floors() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "noise_floor.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _value(node: Any) -> Any:
    if isinstance(node, dict) and {"v", "src", "conf"} <= set(node):
        return node.get("v")
    return node


def _source_ids(node: Any) -> list[str]:
    if isinstance(node, dict) and {"v", "src", "conf"} <= set(node):
        return [source_id for source_id in node.get("src", []) if isinstance(source_id, str)]
    return []


def _claim_source_ids(claim: dict[str, Any]) -> list[str]:
    return [source_id for source_id in claim.get("src", []) if isinstance(source_id, str)]


def _is_unknown(node: Any) -> bool:
    return isinstance(node, dict) and node.get("conf") == "unknown"


def _is_true(node: Any) -> bool:
    return _value(node) is True


def _disclosed(node: Any) -> bool:
    if _is_unknown(node):
        return False
    value = _value(node)
    if value is None:
        return False
    if value is False:
        return False
    if isinstance(value, str):
        return value != "undisclosed"
    return True


def _numeric_value(node: Any, default: float) -> float:
    value = _value(node)
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _months_value(node: Any) -> float:
    value = _value(node)
    if isinstance(value, bool) or value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return 0.0

    lowered = value.strip().lower()
    if not lowered:
        return 0.0
    if "year" in lowered:
        number = _first_number(lowered)
        return number * 12 if number is not None else 12.0
    if "annual" in lowered:
        return 12.0
    number = _first_number(lowered)
    return number if number is not None else 0.0


def _first_number(text: str) -> float | None:
    current = []
    for character in text:
        if character.isdigit() or character == ".":
            current.append(character)
        elif current:
            break
    if not current:
        return None
    return float("".join(current))


def _normalize_domain(domain: str) -> str:
    normalized = domain.strip().lower()
    if normalized.startswith("www."):
        normalized = normalized[4:]
    return normalized.split(":", 1)[0]


def _distinct_nonempty_strings(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    result = set()
    for item in value:
        if isinstance(item, str):
            normalized = item.strip()
            if normalized:
                result.add(normalized)
    return result
