# Task 6 Report: Cached Network Adapters

## Outcome

Implemented stdlib-only cached HTTP adapters for Tavily and GitHub, plus thin
CLI shims and regression tests that lock the cache-key, credential, snapshot,
and validation behavior.

## Files Changed

- `tools/aris_geo/http.py`
- `tools/aris_geo/tavily.py`
- `tools/aris_geo/github.py`
- `tools/tavily_client.py`
- `tools/gh_health.py`
- `tools/aris_geo/__init__.py`
- `tests/test_network_adapters.py`
- `.superpowers/sdd/2026-07-31-vertical-slice/task-6-report.md`

## What Changed

- Added shared HTTP request/response dataclasses and a `urllib.request`-based
  default transport.
- Added canonical request hashing that:
  - uppercases the method;
  - normalizes JSON bodies;
  - excludes `Authorization` / `Proxy-Authorization` from the cache key.
- Added atomic JSON snapshot/cache writes via temp file + `os.replace`.
- Added Tavily client behavior for:
  - safe cache hits without credentials or transport calls;
  - live-miss credential enforcement;
  - HTTP status validation;
  - JSON-shape validation requiring a `results` list;
  - snapshot/cache payloads containing `fetched_at`, `sha256`, and `content`;
  - token-free errors and persisted artifacts.
- Added GitHub health client behavior for:
  - cached per-request JSON fetches;
  - raw, category-neutral repository metrics only;
  - validation of repo/list response shapes before caching.
- Added thin CLI adapters:
  - `tools/tavily_client.py`
  - `tools/gh_health.py`
- Exported the new adapter surface from `tools.aris_geo.__init__`.

## Verification

- RED:
  - `python3 -m unittest tests.test_network_adapters -v`
  - failed with `ModuleNotFoundError: No module named 'tools.aris_geo.github'`
- GREEN:
  - `python3 -m unittest tests.test_network_adapters -v`
  - passed (`7` tests)
- Syntax:
  - `python3 -m py_compile tools/aris_geo/http.py tools/aris_geo/tavily.py tools/aris_geo/github.py tools/tavily_client.py tools/gh_health.py tests/test_network_adapters.py`
  - passed
- Regression:
  - `python3 -m unittest discover -s tests -v`
  - passed (`74` tests)

## Notes

- Cache hits remain usable without credentials only when a valid cached snapshot
  already exists.
- GitHub aggregation intentionally stays minimal in this task:
  request-level caching and raw metric extraction only; no pagination or
  rate-limit orchestration was added.

## Fix Round 1

- Added a GitHub aggregate repo-health snapshot keyed by normalized
  `owner/repo` plus adapter schema version, independent of moving request
  timestamps.
- Added aggregate-cache-first collection behavior:
  - cache hit succeeds without token or transport calls;
  - aggregate cache miss requires a non-empty token before any transport call.
- Strengthened canonical request redaction to remove:
  - URL userinfo;
  - sensitive query keys such as `api_key`, `token`, `access_token`,
    `authorization`, `secret`, and `signature`;
  - sensitive headers such as `x-api-key`, `api-key`, `x-auth-token`,
    `cookie`, and `set-cookie`.
- Ensured non-secret query params and headers still differentiate cache keys.
- Ensured tampered aggregate snapshots are not trusted:
  - without token, the adapter fails safely before transport;
  - with token, the adapter bypasses endpoint caches and performs a fresh live
    refetch before rewriting the aggregate snapshot.

### Fix Round 1 Verification

- RED:
  - `python3 -m unittest tests.test_network_adapters -v`
  - failed on missing aggregate cache contract and insufficient secret redaction
- GREEN:
  - `python3 -m unittest tests.test_network_adapters -v`
  - passed (`13` tests)
- Syntax:
  - `python3 -m py_compile tools/aris_geo/http.py tools/aris_geo/github.py tools/aris_geo/tavily.py tools/tavily_client.py tools/gh_health.py tests/test_network_adapters.py`
  - passed
- Regression:
  - `python3 -m unittest discover -s tests -v`
  - passed (`80` tests)
