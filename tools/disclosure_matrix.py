"""Compute the disclosure matrix: how many of the profiled products actually
publish each field.

The report's core claim is that most GEO monitoring vendors do not disclose the
things a buyer needs. That claim is only worth anything if it is counted rather
than asserted, so this reads `wiki/products/*.json` and reports, per field, how
many dossiers carry a sourced value versus `unknown`.

The counting and rendering live in `tools/aris_geo/disclosure.py` so that this
script and the installed `geo-monitor-audit disclosure` command share one
implementation.

Usage:
    python3 tools/disclosure_matrix.py              # render markdown to stdout
    python3 tools/disclosure_matrix.py --json       # machine-readable
    python3 tools/disclosure_matrix.py --write      # refresh docs/DISCLOSURE_MATRIX.md
    python3 tools/disclosure_matrix.py --check      # fail if the doc is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.aris_geo.compiler import find_repo_root
from tools.aris_geo.disclosure import (  # noqa: F401 — re-exported for tests
    GROUPS,
    MARKER_END,
    MARKER_START,
    compute,
    load_profiles,
    render,
    wrap as _wrap,
)

DOC_RELATIVE = Path("docs/DISCLOSURE_MATRIX.md")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit the raw counts.")
    parser.add_argument("--write", action="store_true", help="Refresh the rendered doc.")
    parser.add_argument("--check", action="store_true", help="Fail if the rendered doc is stale.")
    args = parser.parse_args(argv)

    repo_root = find_repo_root()
    report = compute(load_profiles(repo_root))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    rendered = _wrap(render(report))
    target = repo_root / DOC_RELATIVE

    if args.check:
        if not target.is_file():
            print(f"{DOC_RELATIVE} is missing", file=sys.stderr)
            return 1
        if target.read_text(encoding="utf-8") != rendered:
            print(f"{DOC_RELATIVE} is stale", file=sys.stderr)
            return 1
        return 0

    if args.write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        return 0

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
