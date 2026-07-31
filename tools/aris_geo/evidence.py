from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .schema import EVIDENCE_KINDS, SCHEMA_VERSION, VALID_CONFIDENCE, Envelope, iter_envelopes


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    envelopes_by_path: dict[str, Envelope] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unknown_entry_path(entry: Any) -> str:
    if not isinstance(entry, str):
        return str(entry)
    for separator in (" —— ", " -- ", " - ", "——", "--"):
        if separator in entry:
            return entry.split(separator, 1)[0].strip()
    return entry.strip()


def _validate_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _resolve_excerpt_path(repo_root: Path, evidence_id: str, excerpt_path: Any, errors: list[str]) -> Path | None:
    if not isinstance(excerpt_path, str) or not excerpt_path.strip():
        errors.append(f"evidence {evidence_id}: missing excerpt_path")
        return None

    repo_root = repo_root.resolve()
    candidate = (repo_root / excerpt_path).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError:
        errors.append(f"evidence {evidence_id}: excerpt_path escapes repository root")
        return None
    return candidate


def _validate_evidence_record(record: Any, repo_root: Path, report: ValidationReport) -> None:
    if not isinstance(record, dict):
        report.errors.append("evidence entry must be an object")
        return

    evidence_id = record.get("id")
    if not isinstance(evidence_id, str) or not evidence_id.strip():
        report.errors.append("evidence entry missing id")
        return

    report.evidence_by_id[evidence_id] = record

    if not isinstance(record.get("url"), str) or not record["url"].strip():
        report.errors.append(f"evidence {evidence_id}: missing url")

    if record.get("kind") not in EVIDENCE_KINDS:
        report.errors.append(f"evidence {evidence_id}: invalid kind")

    if not _validate_iso_date(record.get("fetched_at")):
        report.errors.append(f"evidence {evidence_id}: fetched_at must be ISO date")

    if not isinstance(record.get("sha256"), str) or len(record["sha256"]) != 64:
        report.errors.append(f"evidence {evidence_id}: sha256 must be 64 hex characters")

    resolved_path = _resolve_excerpt_path(repo_root, evidence_id, record.get("excerpt_path"), report.errors)
    if resolved_path is None:
        return

    if not resolved_path.is_file():
        report.errors.append(f"evidence {evidence_id}: excerpt file missing at {record.get('excerpt_path')}")
        return

    if sha256_file(resolved_path) != record.get("sha256"):
        report.errors.append(f"evidence {evidence_id}: sha256 mismatch for {record.get('excerpt_path')}")


def validate_profile(profile: dict[str, Any], repo_root: str | Path, strict: bool = True) -> ValidationReport:
    del strict  # Reserved for future gating modes; the vertical slice uses strict validation only.

    report = ValidationReport()
    repo_root = Path(repo_root)

    if profile.get("schema_version") != SCHEMA_VERSION:
        report.errors.append(f"schema_version must be {SCHEMA_VERSION}")

    evidence = profile.get("evidence")
    if not isinstance(evidence, list):
        report.errors.append("evidence must be a list")
        evidence = []

    for record in evidence:
        _validate_evidence_record(record, repo_root, report)

    actual_unknowns: set[str] = set()
    for envelope in iter_envelopes(profile):
        report.envelopes_by_path[envelope.path] = envelope

        if envelope.confidence not in VALID_CONFIDENCE:
            report.errors.append(f"{envelope.path}: invalid conf {envelope.confidence!r}")
            continue

        if envelope.confidence == "unknown":
            if envelope.value is not None:
                report.errors.append(f"{envelope.path}: unknown envelopes must use null values")
            if envelope.source_ids:
                report.errors.append(f"{envelope.path}: unknown envelopes must not include sources")
            actual_unknowns.add(envelope.path)
            continue

        if not envelope.source_ids:
            report.errors.append(f"{envelope.path}: non-unknown envelopes require at least one source")
        for source_id in envelope.source_ids:
            if source_id not in report.evidence_by_id:
                report.errors.append(f"{envelope.path}: unknown source id {source_id}")

        if envelope.confidence == "inferred" and not (isinstance(envelope.note, str) and envelope.note.strip()):
            report.errors.append(f"{envelope.path}: inferred envelopes require a non-empty note")

    declared_unknowns = profile.get("unknowns")
    if not isinstance(declared_unknowns, list):
        report.errors.append("unknowns must be a list")
        declared_paths: set[str] = set()
    else:
        declared_paths = {_unknown_entry_path(entry) for entry in declared_unknowns}

    for path in sorted(actual_unknowns - declared_paths):
        report.errors.append(f"unknowns[] mismatch: missing {path}")
    for path in sorted(declared_paths - actual_unknowns):
        report.errors.append(f"unknowns[] mismatch: extra {path}")

    return report
