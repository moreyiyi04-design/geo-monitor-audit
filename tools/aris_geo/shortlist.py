from __future__ import annotations

from typing import Any


KINDS = frozenset({"commercial", "open-source", "research"})
STATUSES = frozenset({"selected_poc", "watch", "research_reference"})
OPEN_SOURCE_REQUIRED_GATES = frozenset(
    {
        "runnable_code",
        "license",
        "raw_results",
        "reproducible_setup",
        "tests_or_benchmark",
    }
)
REQUIRED_LIST_FIELDS = (
    "scenarios",
    "why_selected",
    "evidence_basis",
    "limitations",
)
REQUIRED_TEXT_FIELDS = ("solves", "replacement_gap")


def validate_shortlist(
    payload: dict[str, Any],
    profile_slugs: set[str],
) -> list[str]:
    errors: list[str] = []
    max_unique = payload.get("max_unique")
    if isinstance(max_unique, bool) or not isinstance(max_unique, int) or not 1 <= max_unique <= 8:
        errors.append("max_unique must be between 1 and 8")

    entries = payload.get("entries")
    if not isinstance(entries, list):
        return [*errors, "entries must be a list"]

    seen: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entry {index}: must be an object")
            continue

        slug = _text(entry.get("slug")) or f"entry {index}"
        if slug in seen:
            errors.append(f"duplicate slug: {slug}")
        seen.add(slug)
        if slug not in profile_slugs:
            errors.append(f"unknown profile slug: {slug}")

        kind = entry.get("kind")
        status = entry.get("status")
        if kind not in KINDS:
            errors.append(f"{slug}: invalid kind: {kind}")
        if status not in STATUSES:
            errors.append(f"{slug}: invalid status: {status}")
        if kind == "research" and status == "selected_poc":
            errors.append(f"{slug}: research entries cannot be selected_poc")

        for field in REQUIRED_LIST_FIELDS:
            if not _nonempty_text_list(entry.get(field)):
                errors.append(f"{slug}: {field} must be non-empty")
        for field in REQUIRED_TEXT_FIELDS:
            if not _text(entry.get(field)):
                errors.append(f"{slug}: {field} must be non-empty")

        if kind == "open-source":
            gates = entry.get("open_source_gates")
            if not isinstance(gates, dict):
                errors.append(f"{slug}: open_source_gates must be an object")
            elif status == "selected_poc":
                for gate in sorted(OPEN_SOURCE_REQUIRED_GATES):
                    if gates.get(gate) is not True:
                        errors.append(
                            f"{slug}: selected open-source entry failed gate: {gate}"
                        )

    if len(seen) > 8:
        errors.append(f"shortlist has {len(seen)} unique entries; maximum is 8")
    elif isinstance(max_unique, int) and not isinstance(max_unique, bool) and len(seen) > max_unique:
        errors.append(
            f"shortlist has {len(seen)} unique entries; configured maximum is {max_unique}"
        )
    return errors


def _nonempty_text_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(bool(_text(item)) for item in value)
    )


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""
