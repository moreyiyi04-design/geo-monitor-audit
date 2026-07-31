from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator


SCHEMA_VERSION = "v1"
VALID_CONFIDENCE = frozenset({"stated", "inferred", "unknown"})
EVIDENCE_KINDS = frozenset(
    {
        "regulatory_authoritative",
        "academic",
        "methodology_doc",
        "third_party_dataset",
        "third_party_report",
        "registry",
        "repo",
        "vendor_doc",
        "vendor_pricing_page",
        "vendor_marketing",
        "community",
    }
)
COMPUTED_SUBTREES = frozenset(
    {
        "audit",
        "evidence",
        "observations",
        "oss_health",
        "risk_flags",
        "scores",
        "unknowns",
        "unresolved",
    }
)
ALLOWED_PLAIN_SCALAR_PATHS = frozenset(
    {
        "schema_version",
        "slug",
        "market",
        "openness",
        "category[]",
        "vendor_domains[]",
        "unknowns[]",
        "evidence[].id",
        "evidence[].url",
        "evidence[].kind",
        "evidence[].fetched_at",
        "evidence[].sha256",
        "evidence[].excerpt_path",
        "evidence[].paid_placement_suspected",
        "features[].name",
        "features[].src[]",
        "effect_claims[].claim",
        "effect_claims[].has_number",
        "effect_claims[].has_denominator",
        "effect_claims[].has_timeframe",
        "effect_claims[].engine",
        "effect_claims[].claimed_change_pp",
        "effect_claims[].grade_proposed",
        "effect_claims[].grade_final",
        "effect_claims[].src[]",
        "tactics.spectrum",
        "tactics.poisoning_fingerprints[]",
        "pricing.cost_per_prompt_month",
        "case_studies[].brand",
        "case_studies[].cross_verified",
        "case_studies[].src[]",
    }
)
ALLOWED_EMPTY_CONTAINER_PATHS = frozenset(
    {
        "category",
        "vendor_domains",
        "unknowns",
        "evidence",
        "features",
        "effect_claims",
        "case_studies",
        "tactics.poisoning_fingerprints",
    }
)


@dataclass(frozen=True)
class Envelope:
    path: str
    value: Any
    source_ids: tuple[str, ...]
    confidence: str
    note: str | None
    raw: dict[str, Any]


def _is_envelope(node: Any) -> bool:
    return isinstance(node, dict) and {"v", "src", "conf"} <= set(node)


def _join_path(base: str, part: str) -> str:
    return f"{base}.{part}" if base else part


def _normalize_path(path: str) -> str:
    return __import__("re").sub(r"\[\d+\]", "[]", path)


def _raw_type_name(node: Any) -> str:
    if node is None:
        return "null"
    return type(node).__name__


def validate_plain_structure(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def walk(node: Any, path: str) -> None:
        if _is_envelope(node):
            return

        normalized = _normalize_path(path)
        if isinstance(node, dict):
            if not node:
                if normalized not in ALLOWED_EMPTY_CONTAINER_PATHS:
                    errors.append(f"{path or '<root>'}: empty object is not allowed")
                return
            for key, value in node.items():
                if key in COMPUTED_SUBTREES:
                    continue
                walk(value, _join_path(path, key))
            return

        if isinstance(node, list):
            if not node:
                if normalized not in ALLOWED_EMPTY_CONTAINER_PATHS:
                    errors.append(f"{path or '<root>'}: empty list is not allowed")
                return
            for index, value in enumerate(node):
                child_path = f"{path}[{index}]" if path else f"[{index}]"
                walk(value, child_path)
            return

        if normalized not in ALLOWED_PLAIN_SCALAR_PATHS:
            errors.append(f"{path or '<root>'}: expected envelope, found raw {_raw_type_name(node)}")

    walk(profile, "")
    return errors


def iter_envelopes(profile: dict[str, Any]) -> Iterator[Envelope]:
    def walk(node: Any, path: str) -> Iterator[Envelope]:
        if _is_envelope(node):
            note = node.get("note")
            yield Envelope(
                path=path,
                value=node.get("v"),
                source_ids=tuple(node.get("src", [])),
                confidence=node.get("conf"),
                note=note if isinstance(note, str) else None,
                raw=node,
            )
            return

        if isinstance(node, dict):
            for key, value in node.items():
                if key in COMPUTED_SUBTREES:
                    continue
                yield from walk(value, _join_path(path, key))
            return

        if isinstance(node, list):
            for index, value in enumerate(node):
                child_path = f"{path}[{index}]" if path else f"[{index}]"
                yield from walk(value, child_path)

    yield from walk(profile, "")
