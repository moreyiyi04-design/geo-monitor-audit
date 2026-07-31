# ARIS-GEO Vertical Slice Design

## Purpose

Implement the first executable ARIS-GEO increment described by
`docs/DESIGN.md`: one offline-reproducible Profound product can travel through
evidence validation, deterministic scoring, persona review staging, profile
verification, and README compilation. Live Tavily, GitHub, and ARIS execution
remain explicit adapters around this deterministic core.

## Scope

The increment includes:

- the repository layout and six ARIS skill contracts;
- a versioned product schema and evidence-envelope traversal rules;
- deterministic evidence, confidence, grade, hash, and unknown-field checks;
- deterministic scores and automatically derived risk flags;
- persona inbox staging with filesystem-enforced visibility;
- an idempotent per-product state machine with bounded review rounds;
- ARIS JSON-result validation, including compaction and denied-tool detection;
- cached HTTP adapters for Tavily and the public GitHub API;
- byte-reproducible README compiled sections;
- a Profound offline fixture that exercises the complete deterministic path;
- standard-library unit and integration tests, plus GitHub Actions checks.

The increment does not claim that live research has been completed. It does
not ship fabricated Profound facts, call remote services in CI, or implement a
production-scale candidate discovery strategy.

## Architecture

`tools/aris_geo/` is an importable standard-library-only package. Each module
has one responsibility: schema traversal, evidence validation, grading,
scoring, risk derivation, README rendering, state persistence, persona
staging, ARIS invocation, HTTP caching, and orchestration. `tools/*.py` are
thin command-line adapters.

All model and network boundaries use injected callables or subprocess
adapters. Unit and integration tests use local files and deterministic fake
responses. The orchestrator owns phase transitions; skills only transform the
files made visible in their working directory.

The canonical data flow is:

`raw evidence -> draft profile -> isolated vendor/skeptic reviews -> arbiter
patch -> deterministic apply -> verify/score -> compiled README`.

## Data Contracts

Every research-derived leaf is an envelope:

```json
{"v": "value", "src": ["e1"], "conf": "stated"}
```

`conf` is one of `stated`, `inferred`, or `unknown`. Unknown envelopes have a
null value and no source IDs. Inferred envelopes require a non-empty note.
Computed subtrees (`scores`, automatic risk flags, audit counters, and
GitHub-derived health metrics) are excluded from evidence-envelope traversal.

Evidence records use the kinds and required fields defined in the v1 design.
The verifier resolves excerpt paths beneath the repository root, prevents
path escape, recomputes SHA-256, validates source references, and performs a
two-way comparison between unknown envelopes and `unknowns[]`.

Effect grades are recalculated from evidence kinds, source domains, suspected
paid placement, claim structure, and noise-floor thresholds. Stored final
grades must match the recalculated grade.

## Failure Semantics

A phase fails on a non-zero ARIS exit, invalid JSON output, automatic
compaction, a denied tool result, excessive iterations, a missing required
file read, invalid output schema, or a deterministic gate failure. The driver
records the error in `wiki/state/<slug>.json`, advances no downstream phase,
and can continue with the next product.

Writes use temporary files followed by `os.replace`. A product that reached
`PASS` is skipped unless its evidence fingerprint changes. Review retries are
bounded at three rounds.

## Testing

Tests use `unittest` so a fresh Python 3 installation is sufficient. Each
production behavior starts with a failing test. Coverage includes:

- valid and invalid evidence envelopes;
- hash tampering and path traversal;
- A/B source-domain downgrades and noise-floor downgrades;
- exact score recomputation;
- README byte comparison while preserving the handwritten block;
- persona visibility boundaries;
- ARIS compaction and deny rejection;
- state-machine resume and evidence invalidation;
- an offline Profound fixture through all deterministic phases.

CI runs unit tests, strict evidence verification, score checking, and README
reproducibility checks without secrets or network access.

## Completion Criteria

The vertical slice is complete when:

1. `python3 -m unittest discover -s tests -v` passes;
2. `python3 tools/verify_evidence.py --strict` passes on committed fixtures;
3. `python3 tools/score.py --check` passes;
4. `python3 tools/compile_readme.py --check` passes;
5. fault-injection tests prove tampered evidence, persona leakage, denied
   tools, and stale computed output are rejected;
6. the README documents exact offline and live smoke commands without
   claiming that credentials or ARIS are bundled.

