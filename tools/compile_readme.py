from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.aris_geo.compiler import compile_readme, find_repo_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile the README compiled block from wiki profiles.")
    parser.add_argument("--check", action="store_true", help="Fail if README.md is stale without rewriting it.")
    args = parser.parse_args(argv)

    try:
        repo_root = find_repo_root()
        readme, rendered = compile_readme(repo_root)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if readme == rendered:
        return 0

    readme_path = repo_root / "README.md"
    if args.check:
        print("README compiled block is stale", file=sys.stderr)
        return 1

    _atomic_write(readme_path, rendered)
    return 0


def _atomic_write(path: Path, content: str) -> None:
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
