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
