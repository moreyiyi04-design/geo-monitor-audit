from __future__ import annotations

import argparse
from pathlib import Path

from tools.aris_geo.staging import stage_persona_inbox


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage a persona-specific ARIS inbox.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--slug", required=True)
    parser.add_argument("--persona", required=True, choices=("vendor", "skeptic", "arbiter"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    inbox = stage_persona_inbox(args.repo_root, args.slug, args.persona)
    print(inbox)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
