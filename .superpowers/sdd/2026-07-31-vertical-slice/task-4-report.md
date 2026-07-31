# Task 4 Report: Persona staging and ARIS result contract

## Scope

Implemented the Task 4 contract in:

- `tools/aris_geo/staging.py`
- `tools/aris_geo/aris.py`
- `tools/stage_inbox.py`
- `tools/aris_geo/__init__.py`
- `tests/test_staging.py`
- `tests/test_aris.py`

## TDD cycle

### RED

Ran:

```bash
python3 -m unittest tests.test_staging tests.test_aris -v
```

Observed expected missing-implementation failures:

- `ModuleNotFoundError: No module named 'tools.aris_geo.staging'`
- `ModuleNotFoundError: No module named 'tools.aris_geo.aris'`

### GREEN

Implemented:

- persona inbox staging with an explicit allowlist per persona;
- slug validation to block path-segment escape attempts;
- symlink rejection on staged sources;
- isolated vendor/skeptic inboxes and arbiter-only review aggregation;
- strict ARIS JSON parsing into `ArisResult`;
- rejection of invalid JSON, auto-compaction, permission-denied tool results,
  excessive iterations, and missing required tools;
- ARIS runner wiring that always uses `prompt`, `workspace-write`,
  allowlisted tools, and the staged inbox `--cwd`;
- a thin `tools/stage_inbox.py` CLI wrapper.

## Verification

Targeted tests:

```bash
python3 -m unittest tests.test_staging tests.test_aris -v
```

Result: `12` tests passed.

Full suite:

```bash
python3 -m unittest discover -s tests -v
```

Result: `46` tests passed.

Syntax check:

```bash
python3 -m py_compile \
  tools/aris_geo/staging.py \
  tools/aris_geo/aris.py \
  tools/stage_inbox.py \
  tests/test_staging.py \
  tests/test_aris.py
```

Result: passed.

## Simplifications made

- Kept staging logic file-based and explicit instead of adding a generic copy
  framework.
- Used an injected runner for `run_aris_phase(...)` so unit tests stay fully
  offline and avoid subprocess mocking libraries.
- Kept permission-denial detection text-based over the full structured result
  payload so the parser tolerates minor ARIS shape differences while still
  enforcing the deny contract.

## Remaining risks

- The deny-result detector is intentionally defensive and string-based because
  the exact ARIS structured deny schema is not yet fixture-backed in-repo.
- LSP diagnostics tooling was not available in this task environment, so
  verification used the full unit suite plus `py_compile`.

## Fix round 1

### Contract tightened

- deny detection no longer scans every successful `tool_result` payload for
  free-text denial phrases;
- deny rejection now keys off structured deny/error signals first and only
  inspects denial text within error-shaped fields;
- `usage` now requires the four control-signal fields:
  `input_tokens`, `output_tokens`, `cache_creation_input_tokens`,
  `cache_read_input_tokens`;
- each required `usage` field must be present, numeric, non-bool, and
  non-negative.

### RED

Ran:

```bash
python3 -m unittest tests.test_aris -v
```

Observed expected failures:

- successful `read_file` content containing `permission denied` was falsely
  rejected;
- deny-shaped `status: "denied"` result was missed;
- missing / bool / negative / string `usage` fields were accepted.

### GREEN

Implemented:

- structured deny detection via `status`, `permission`, `denied`, and
  `error.type`;
- denial-text inspection limited to error-shaped `error` / `message` /
  `content` fields when `is_error == true`;
- strict validation for the four required `usage` counters.

### Verification

```bash
python3 -m unittest tests.test_aris -v
python3 -m unittest discover -s tests -v
python3 -m py_compile \
  tools/aris_geo/staging.py \
  tools/aris_geo/aris.py \
  tools/stage_inbox.py \
  tests/test_staging.py \
  tests/test_aris.py
```

Results:

- focused ARIS tests: `12` passed;
- full suite: `50` passed;
- syntax check: passed.
