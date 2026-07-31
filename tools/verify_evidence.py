from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.aris_geo.compiler import find_repo_root
from tools.aris_geo.evidence import validate_profile
from tools.aris_geo.grading import final_grade
from tools.aris_geo.scoring import _load_noise_floors, _vendor_domains


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate evidence envelopes and stored effect grades.")
    parser.add_argument("--strict", action="store_true", help="Run the strict repository evidence gate.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        repo_root = find_repo_root()
        profile_paths = _profile_paths(repo_root)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    errors: list[str] = []
    for path in profile_paths:
        errors.extend(_validate_profile_path(path, repo_root, strict=args.strict))

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    return 0


def _profile_paths(repo_root: Path) -> list[Path]:
    products_dir = repo_root / "wiki" / "products"
    if not products_dir.is_dir():
        raise FileNotFoundError(f"missing products directory: {products_dir}")
    return sorted(path for path in products_dir.glob("*.json") if path.is_file())


def _validate_profile_path(path: Path, repo_root: Path, *, strict: bool) -> list[str]:
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path.name}: invalid JSON ({exc.msg})"]
    if not isinstance(profile, dict):
        return [f"{path.name}: top-level JSON must be an object"]

    report = validate_profile(profile, repo_root, strict=strict)
    errors = [f"{path.name}: {message}" for message in report.errors]
    evidence_by_id = report.evidence_by_id
    vendor_domains = _vendor_domains(profile)
    noise_floors = _load_noise_floors()

    for index, claim in enumerate(profile.get("effect_claims") or []):
        claim_path = f"{path.name}: effect_claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{claim_path}: claim must be an object")
            continue
        for source_id in claim.get("src", []):
            if isinstance(source_id, str) and source_id not in evidence_by_id:
                errors.append(f"{claim_path}: unknown source id {source_id}")
        expected_grade = final_grade(claim, evidence_by_id, vendor_domains, noise_floors)
        actual_grade = claim.get("grade_final")
        if actual_grade != expected_grade:
            errors.append(
                f"{claim_path}: grade_final mismatch (stored {actual_grade!r}, expected {expected_grade!r})"
            )
    return errors


if __name__ == "__main__":
    raise SystemExit(main())
