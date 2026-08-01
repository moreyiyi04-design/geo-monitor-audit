#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.aris_geo.publication import build_publication
from tools.aris_geo.shortlist import validate_shortlist


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build evidence files and product profiles from the curated public-source catalog."
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=Path("wiki/catalog.json"),
        help="catalog path relative to the repository root",
    )
    return parser.parse_args(argv)


def validate_committed_shortlist(repo_root: Path, shortlist_path: Path) -> None:
    payload = json.loads(shortlist_path.read_text(encoding="utf-8"))
    profile_slugs = {
        path.stem
        for path in (repo_root / "wiki" / "products").glob("*.json")
    }
    errors = validate_shortlist(payload, profile_slugs)
    if errors:
        formatted = "\n".join(f"- {error}" for error in errors)
        raise ValueError(f"invalid shortlist:\n{formatted}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    catalog_path = args.catalog
    if not catalog_path.is_absolute():
        catalog_path = REPO_ROOT / catalog_path
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    profiles = build_publication(REPO_ROOT, catalog)
    validate_committed_shortlist(
        REPO_ROOT,
        REPO_ROOT / "wiki" / "shortlist.json",
    )
    print(f"built {len(profiles)} product profiles")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
