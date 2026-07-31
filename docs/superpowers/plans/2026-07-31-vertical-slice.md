# ARIS-GEO Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one offline-reproducible Profound vertical slice through ARIS-GEO's deterministic evidence, review, scoring, and README pipeline.

**Architecture:** A standard-library Python package contains pure deterministic
logic and narrow adapters. Thin CLI scripts call that package. Network and
model execution sit behind injected boundaries so CI is offline and
reproducible.

**Tech Stack:** Python 3.11+ standard library, JSON, Markdown, `unittest`,
GitHub Actions, ARIS-Code v0.4.21+ for optional live execution.

## Global Constraints

- Python production code has zero third-party dependencies.
- Models never receive network credentials and never compute scores.
- Every non-unknown research value references committed evidence.
- Persona isolation is enforced by staged filesystem contents.
- README compiled bytes are generated solely from wiki data.
- Tests run without network access, credentials, or ARIS installed.

---

### Task 1: Schema and evidence envelopes

**Files:**
- Create: `tools/aris_geo/__init__.py`
- Create: `tools/aris_geo/schema.py`
- Create: `tools/aris_geo/evidence.py`
- Create: `tests/test_evidence.py`

**Interfaces:**
- Produces: `iter_envelopes(profile)`, `validate_profile(profile, repo_root,
  strict=True) -> ValidationReport`, and `sha256_file(path) -> str`.

- [ ] Write tests for envelope discovery, source resolution, inferred notes,
  unknown symmetry, hash mismatch, and excerpt path escape.
- [ ] Run `python3 -m unittest tests.test_evidence -v`; confirm failures are
  caused by missing modules.
- [ ] Implement the minimal traversal and validation types.
- [ ] Re-run the test module and confirm it passes.

### Task 2: Claim grading and deterministic scores

**Files:**
- Create: `tools/aris_geo/grading.py`
- Create: `tools/aris_geo/scoring.py`
- Create: `tools/noise_floor.json`
- Create: `tests/test_grading.py`
- Create: `tests/test_scoring.py`

**Interfaces:**
- Consumes: validated profile and evidence maps from Task 1.
- Produces: `final_grade(claim, evidence, vendor_domains, noise_floors)`,
  `calculate_scores(profile)`, and `derive_auto_risk_flags(profile)`.

- [ ] Write failing tests for A-E mechanics, vendor-domain downgrades,
  suspected placements, noise-floor downgrades, all five score dimensions,
  and automatic labels.
- [ ] Run both test modules and confirm missing-function failures.
- [ ] Implement grading, scoring, and risk derivation without mutating input.
- [ ] Re-run both modules and confirm they pass.

### Task 3: README reproducibility

**Files:**
- Create: `tools/aris_geo/compiler.py`
- Create: `tools/compile_readme.py`
- Create: `tests/test_compiler.py`

**Interfaces:**
- Produces: `render_compiled_block(profiles) -> str`,
  `replace_compiled_block(readme, block) -> str`, and CLI `--check`.

- [ ] Write failing tests proving deterministic ordering, handwritten-block
  preservation, missing-marker rejection, and stale-output detection.
- [ ] Run the compiler tests and observe the missing implementation failure.
- [ ] Implement stable Markdown rendering and the thin CLI.
- [ ] Re-run tests and confirm they pass.

### Task 4: Persona staging and ARIS result contract

**Files:**
- Create: `tools/aris_geo/staging.py`
- Create: `tools/aris_geo/aris.py`
- Create: `tools/stage_inbox.py`
- Create: `tests/test_staging.py`
- Create: `tests/test_aris.py`

**Interfaces:**
- Produces: `stage_persona_inbox(...) -> Path`,
  `parse_aris_result(stdout, required_tools=()) -> ArisResult`, and
  `run_aris_phase(...) -> ArisResult`.

- [ ] Write failing tests for vendor/skeptic visibility, arbiter inputs,
  invalid JSON, compaction, deny results, iteration bounds, and required tool
  usage.
- [ ] Run the modules and confirm missing implementation failures.
- [ ] Implement allowlisted copying and strict ARIS JSON parsing.
- [ ] Re-run tests and confirm they pass.

### Task 5: State and orchestration

**Files:**
- Create: `tools/aris_geo/state.py`
- Create: `tools/aris_geo/loop.py`
- Create: `tools/geo_loop.py`
- Create: `tests/test_state.py`
- Create: `tests/test_loop.py`

**Interfaces:**
- Produces: `ProductState`, atomic `load_state`/`save_state`,
  `evidence_fingerprint`, and `GeoLoop.run_product(slug)`.

- [ ] Write failing tests for atomic persistence, phase transitions, pass
  skipping, evidence invalidation, bounded review retry, and next-product
  continuation.
- [ ] Run tests and confirm expected missing implementation failures.
- [ ] Implement the explicit phase state machine and CLI options `--limit`,
  `--budget-tokens`, `--parallel`, and `--refresh-stale`.
- [ ] Re-run tests and confirm they pass.

### Task 6: Cached network adapters

**Files:**
- Create: `tools/aris_geo/http.py`
- Create: `tools/aris_geo/tavily.py`
- Create: `tools/aris_geo/github.py`
- Create: `tools/tavily_client.py`
- Create: `tools/gh_health.py`
- Create: `tests/test_network_adapters.py`

**Interfaces:**
- Produces: injected-transport clients whose cache key is a SHA-256 of the
  normalized request and whose snapshots contain `fetched_at` and content
  hash.

- [ ] Write failing tests with an in-memory transport for cache hits, HTTP
  errors, missing credentials, snapshot hashing, and GitHub health metrics.
- [ ] Run tests and confirm missing implementation failures.
- [ ] Implement clients using `urllib.request`; never log tokens.
- [ ] Re-run tests and confirm they pass.

### Task 7: Skills and deterministic CLI gates

**Files:**
- Create: `skills/geo-seed/SKILL.md`
- Create: `skills/geo-plan-queries/SKILL.md`
- Create: `skills/geo-digest/SKILL.md`
- Create: `skills/geo-profile/SKILL.md`
- Create: `skills/geo-review/SKILL.md`
- Create: `skills/shared/SCHEMA.md`
- Create: `skills/shared/EVIDENCE_RULES.md`
- Create: `skills/shared/GRADING.md`
- Create: `tools/verify_evidence.py`
- Create: `tools/score.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Produces: the exact slash-command contracts used by `geo_loop.py` and
  offline-checkable CLI exit codes.

- [ ] Write failing subprocess tests for successful and failing gate exits.
- [ ] Run the CLI tests and observe missing script failures.
- [ ] Write concise skills and CLI adapters over Tasks 1-2.
- [ ] Re-run tests and confirm they pass.

### Task 8: Profound offline fixture and repository documentation

**Files:**
- Create: `tests/fixtures/profound/wiki/raw/profound/*.txt`
- Create: `tests/fixtures/profound/wiki/products/profound.json`
- Create: `wiki/products/profound.json`
- Create: `wiki/raw/profound/*.txt`
- Create: `wiki/queue.json`
- Create: `README.md`
- Create: `docs/METHODOLOGY.md`
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `.github/workflows/verify.yml`
- Create: `.github/workflows/freshness.yml`
- Create: `tests/test_vertical_slice.py`

**Interfaces:**
- Consumes: all deterministic modules and CLIs.
- Produces: one fully reproducible offline repository state.

- [ ] Create a failing integration test that copies the fixture, verifies its
  profile, recalculates scores, and compiles README.
- [ ] Run the integration test and confirm failure on missing fixture/output.
- [ ] Add minimal, explicitly synthetic test evidence and documentation that
  labels it as a test fixture rather than live research.
- [ ] Generate committed scores and README using production code.
- [ ] Re-run the integration test and confirm it passes.

### Task 9: Full verification and fault injection

**Files:**
- Modify: tests from Tasks 1-8 only when a real uncovered requirement is
  discovered.

**Interfaces:**
- Produces: completion evidence for the entire vertical slice.

- [ ] Run `python3 -m unittest discover -s tests -v`.
- [ ] Run `python3 tools/verify_evidence.py --strict`.
- [ ] Run `python3 tools/score.py --check`.
- [ ] Run `python3 tools/compile_readme.py --check`.
- [ ] Copy the repository to a temporary directory, alter an excerpt byte,
  and confirm strict verification exits non-zero.
- [ ] Confirm no key-like values or generated caches are tracked.

