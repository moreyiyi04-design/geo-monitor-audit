from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.aris_geo.tavily import TavilyClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query Tavily with local request caching.")
    parser.add_argument("query")
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache") / "tavily")
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--api-key-env", default="TAVILY_API_KEY")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = TavilyClient(args.cache_dir, api_key=os.environ.get(args.api_key_env))
    payload = client.search(
        args.query,
        max_results=args.max_results,
        snapshot_path=args.snapshot,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
