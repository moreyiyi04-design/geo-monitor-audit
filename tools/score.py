from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.aris_geo.compiler import find_repo_root
from tools.aris_geo.grading import final_grade
from tools.aris_geo.scoring import (
    _load_noise_floors,
    _vendor_domains,
    calculate_scores,
    derive_auto_risk_flags,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Recompute deterministic grades, scores, and risk flags.")
    parser.add_argument("--check", action="store_true", help="Fail if any computed fields are stale.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        repo_root = find_repo_root()
        product_paths = _product_paths(repo_root)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    stale_paths: list[str] = []
    for path in product_paths:
        try:
            original = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"{path.name}: invalid JSON ({exc.msg})", file=sys.stderr)
            return 2
        if not isinstance(original, dict):
            print(f"{path.name}: top-level JSON must be an object", file=sys.stderr)
            return 2

        updated = _recompute_profile(original)
        if updated == original:
            continue
        if args.check:
            stale_paths.append(path.name)
            continue
        _atomic_write_json(path, updated)

    if stale_paths:
        print(f"stale computed fields: {', '.join(stale_paths)}", file=sys.stderr)
        return 1
    return 0


def _product_paths(repo_root: Path) -> list[Path]:
    products_dir = repo_root / "wiki" / "products"
    if not products_dir.is_dir():
        raise FileNotFoundError(f"missing products directory: {products_dir}")
    return sorted(path for path in products_dir.glob("*.json") if path.is_file())


def _recompute_profile(profile: dict) -> dict:
    updated = copy.deepcopy(profile)
    evidence = {
        record["id"]: record
        for record in updated.get("evidence") or []
        if isinstance(record, dict) and isinstance(record.get("id"), str)
    }
    vendor_domains = _vendor_domains(updated)
    noise_floors = _load_noise_floors()

    for claim in updated.get("effect_claims") or []:
        if isinstance(claim, dict):
            claim["grade_final"] = final_grade(claim, evidence, vendor_domains, noise_floors)

    updated["scores"] = calculate_scores(updated)
    updated["risk_flags"] = derive_auto_risk_flags(updated)
    return updated


def _atomic_write_json(path: Path, payload: dict) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


if __name__ == "__main__":
    raise SystemExit(main())
