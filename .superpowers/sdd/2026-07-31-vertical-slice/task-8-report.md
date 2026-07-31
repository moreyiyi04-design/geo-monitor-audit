# Task 8 Report

## Outcome

Task 8 is complete as an offline, synthetic Profound fixture and repository
documentation slice.

- Added committed synthetic raw evidence under `wiki/raw/profound/` and the
  matching reusable test fixture under `tests/fixtures/profound/`.
- Added a committed synthetic product profile at `wiki/products/profound.json`
  with hashes, unknown symmetry, generated claim grades, deterministic scores,
  and generated risk flags.
- Added repository documentation and policy files: `README.md`,
  `docs/METHODOLOGY.md`, `LICENSE`, `.github/workflows/verify.yml`, and
  `.github/workflows/freshness.yml`.
- Added `tests/test_vertical_slice.py` to prove the fixture can regenerate the
  committed profile and compiled README from production CLIs.
- Added `tools/freshness.py` to keep scheduled freshness checks deterministic
  and stdlib-only.

## Honesty / Scope Notes

- The committed Profound record is explicitly a **synthetic offline fixture**.
- All evidence URLs use `https://example.invalid/...` subdomains and all raw
  excerpts explicitly identify themselves as synthetic test data.
- The README and methodology document do not claim live research, live product
  findings, or a total ranking.
- Live smoke remains documented but intentionally not executed in this task.

## Verification Evidence

- RED: `python3 -m unittest tests.test_vertical_slice -v` initially failed on
  missing `tests/fixtures/profound/wiki/products/profound.json` and missing
  `README.md`.
- GREEN:
  - `python3 tools/score.py` regenerated committed computed fields.
  - `python3 tools/verify_evidence.py --strict` passed on the synthetic profile.
  - `python3 tools/compile_readme.py` regenerated the committed compiled block.
- Final verification:
  - `python3 -m unittest discover -s tests -v` → `Ran 94 tests ... OK`
  - `python3 tools/verify_evidence.py --strict` → exit 0
  - `python3 tools/score.py --check` → exit 0
  - `python3 tools/compile_readme.py --check` → exit 0
  - `python3 tools/freshness.py --days 90 --today 2026-07-31` →
    `all evidence records are within 90 days`
  - `python3 -m py_compile tests/test_vertical_slice.py tools/freshness.py tools/compile_readme.py tools/score.py tools/verify_evidence.py`
    → exit 0
  - `git diff --check` → exit 0

## Remaining Gaps

- No live Tavily, GitHub, or ARIS smoke was run here by design.
- The fixture is intentionally minimal and synthetic; it should not be reused as
  evidence about the real Profound product without replacing every source with
  live research data.
