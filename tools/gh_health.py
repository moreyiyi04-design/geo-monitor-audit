from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from tools.aris_geo.github import GitHubHealthClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch cached raw GitHub repository health metrics.")
    parser.add_argument("repository", help="owner/repo")
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache") / "github")
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    owner, repo = _parse_repository(args.repository)
    client = GitHubHealthClient(args.cache_dir, token=os.environ.get(args.token_env))
    payload = client.repository_health(owner, repo)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _parse_repository(value: str) -> tuple[str, str]:
    parts = [part for part in value.split("/") if part]
    if len(parts) != 2:
        raise SystemExit("repository must be in owner/repo form")
    return parts[0], parts[1]


if __name__ == "__main__":
    raise SystemExit(main())
