from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.aris_geo.loop import GeoLoop


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the ARIS-GEO per-product orchestration loop.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--limit", type=_positive_int)
    parser.add_argument("--budget-tokens", type=_positive_int)
    parser.add_argument("--parallel", type=_positive_int, default=1)
    parser.add_argument("--refresh-stale", type=_positive_int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.parallel > 1:
        print("parallel execution >1 is not implemented in this slice", file=sys.stderr)
        return 2

    loop = GeoLoop(args.repo_root)
    outcomes = loop.run_queue(
        limit=args.limit,
        budget_tokens=args.budget_tokens,
        refresh_stale=args.refresh_stale,
    )
    failures = [outcome for outcome in outcomes if not outcome.ok]
    for outcome in failures:
        print(f"{outcome.slug}: {outcome.status}", file=sys.stderr)
    return 1 if failures else 0


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
