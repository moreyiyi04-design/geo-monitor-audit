from __future__ import annotations

"""Deterministic effect-claim grading.

`final_grade()` is the scoring authority for `effect_claims[*].grade_final`.
It never parses prose. Noise-floor downgrades only consult an explicit
`claimed_change_pp` field on the claim object, measured in percentage points.
When present, `claimed_change_pp` must be an `int` or `float` but not `bool`.
If the field is absent, grading skips the noise-floor comparison entirely.

The `noise_floors` argument is expected to follow `tools/noise_floor.json`:

{
  "engines": {
    "SearchGPT": {
      "attribution_floor_pp": 3.0,
      ...
    }
  }
}
"""

from typing import Any, Iterable
from urllib.parse import urlparse


GRADE_WEIGHTS = {"A": 1.0, "B": 0.75, "C": 0.5, "D": 0.2, "E": 0.0}
INDEPENDENT_A_KINDS = frozenset({"regulatory_authoritative", "academic"})


def final_grade(
    claim: dict[str, Any],
    evidence: dict[str, dict[str, Any]],
    vendor_domains: Iterable[str],
    noise_floors: dict[str, Any],
) -> str:
    source_ids = claim.get("src") or []
    records = [evidence[source_id] for source_id in source_ids if source_id in evidence]
    fallback_grade = _claim_structure_grade(claim)
    candidate = fallback_grade

    if _qualifies_for_a(records, vendor_domains):
        candidate = "A"
    elif _qualifies_for_b(records, vendor_domains):
        candidate = "B"

    claimed_change_pp = _claimed_change_pp(claim)
    if _below_noise_floor(claim, claimed_change_pp, noise_floors):
        return "D"

    return candidate


def _claim_structure_grade(claim: dict[str, Any]) -> str:
    if not claim.get("has_number") or not (claim.get("src") or []):
        return "E"
    if claim.get("has_denominator") or claim.get("has_timeframe"):
        return "C"
    return "D"


def _qualifies_for_a(records: list[dict[str, Any]], vendor_domains: Iterable[str]) -> bool:
    if not records or _all_vendor_hosted(records, vendor_domains):
        return False
    kinds = {record.get("kind") for record in records}
    if kinds & INDEPENDENT_A_KINDS:
        return True
    return "methodology_doc" in kinds and "third_party_dataset" in kinds


def _qualifies_for_b(records: list[dict[str, Any]], vendor_domains: Iterable[str]) -> bool:
    if not records or _all_vendor_hosted(records, vendor_domains):
        return False
    report_records = [record for record in records if record.get("kind") == "third_party_report"]
    if not report_records:
        return False
    return not all(bool(record.get("paid_placement_suspected")) for record in report_records)


def _claimed_change_pp(claim: dict[str, Any]) -> float | None:
    if "claimed_change_pp" not in claim:
        return None
    value = claim["claimed_change_pp"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("claimed_change_pp must be an int or float when present")
    return float(value)


def _below_noise_floor(claim: dict[str, Any], claimed_change_pp: float | None, noise_floors: dict[str, Any]) -> bool:
    if claimed_change_pp is None:
        return False
    engine = claim.get("engine")
    if not isinstance(engine, str) or not engine:
        return False
    engine_record = (noise_floors.get("engines") or {}).get(engine)
    if not isinstance(engine_record, dict):
        return False
    threshold = engine_record.get("attribution_floor_pp")
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        return False
    return claimed_change_pp < float(threshold)


def _all_vendor_hosted(records: list[dict[str, Any]], vendor_domains: Iterable[str]) -> bool:
    domains = {_normalize_domain(domain) for domain in vendor_domains if _normalize_domain(domain)}
    if not records:
        return False
    for record in records:
        domain = _record_domain(record)
        if domain is None or domain not in domains:
            return False
    return True


def _record_domain(record: dict[str, Any]) -> str | None:
    url = record.get("url")
    if not isinstance(url, str) or not url.strip():
        return None
    return _normalize_domain(urlparse(url).netloc or url)


def _normalize_domain(domain: str) -> str:
    normalized = domain.strip().lower()
    if normalized.startswith("www."):
        normalized = normalized[4:]
    return normalized.split(":", 1)[0]
