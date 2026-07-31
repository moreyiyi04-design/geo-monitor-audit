from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
    loop.run_queue(
        limit=args.limit,
        budget_tokens=args.budget_tokens,
        refresh_stale=args.refresh_stale,
    )
    return 0


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
