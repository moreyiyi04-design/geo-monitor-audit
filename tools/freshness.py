from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.aris_geo.compiler import find_repo_root


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report stale evidence records by fetched_at age.")
    parser.add_argument("--days", type=_positive_int, default=90)
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repo_root = find_repo_root()
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    stale = _collect_stale(repo_root, today=args.today, max_age_days=args.days)
    if not stale:
        print(f"all evidence records are within {args.days} days")
        return 0

    for slug, evidence_id, fetched_at, age_days in stale:
        print(f"{slug}:{evidence_id} fetched_at={fetched_at} age_days={age_days}")
    return 1


def _collect_stale(repo_root: Path, *, today: date, max_age_days: int) -> list[tuple[str, str, str, int]]:
    stale: list[tuple[str, str, str, int]] = []
    products_dir = repo_root / "wiki" / "products"
    for path in sorted(products_dir.glob("*.json")):
        profile = json.loads(path.read_text(encoding="utf-8"))
        slug = str(profile.get("slug") or path.stem)
        for record in profile.get("evidence") or []:
            if not isinstance(record, dict):
                continue
            fetched_at = record.get("fetched_at")
            evidence_id = str(record.get("id") or "?")
            if not isinstance(fetched_at, str):
                continue
            age_days = (today - date.fromisoformat(fetched_at)).days
            if age_days > max_age_days:
                stale.append((slug, evidence_id, fetched_at, age_days))
    return stale


def _positive_int(raw: str) -> int:
    value = int(raw)
    if value <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
