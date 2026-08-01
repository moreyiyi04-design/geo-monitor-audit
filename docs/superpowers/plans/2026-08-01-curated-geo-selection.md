# Curated GEO Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the public product inventory with a small, scenario-driven shortlist that selects commercial and open-source candidates by user value and evidence rather than discoverability or volume.

**Architecture:** `wiki/market-map.json` remains the internal discovery pool. A new reviewed `wiki/shortlist.json` records no more than eight unique public candidates with status, scenario value, evidence rationale, limitations, and replacement gap; `tools/aris_geo/shortlist.py` validates that contract. `docs/FINAL_REPORT.md` and README consume the curated decision, while the README compiler stops rendering the 112-object map.

**Tech Stack:** Python 3.11+, JSON, Markdown, unittest

## Global Constraints

- No new dependencies.
- The governing principle must appear verbatim in the public report: `我觉得在精不在多，列出来了100个甚至一千个烂产品不如精选出来真正的有效的能帮助各类用户在各种场景下解决问题的产品。`
- The public shortlist contains no more than eight unique products or projects.
- One qualified product may serve multiple scenarios.
- A scenario may have zero recommendations.
- Commercial products and open-source projects use separate hard gates.
- Vendor claims justify PoC priority, not independent proof of outcomes.
- `wiki/market-map.json` remains available for research but is not rendered in README or the final report.
- Scores, risk flags, profiles, and evidence hashes remain machine-readable and reproducible.

---

### Task 1: Lock the curated public surface

**Files:**
- Modify: `tests/test_compiler.py`
- Modify: `tests/test_vertical_slice.py`

**Interfaces:**
- Consumes: `render_compiled_block(profiles, market_map)` from `tools.aris_geo.compiler`.
- Produces: tests requiring a dated research note with no global market table, and a final report that states the shortlist contract.

- [ ] **Step 1: Write the failing compiler test**

Replace the global-map rendering expectation with:

```python
block = render_compiled_block([profile], market_map)
self.assertIn("完整候选池保留在 wiki/market-map.json", block)
self.assertNotIn("### 附录：全球市场地图", block)
self.assertNotIn("| Alpha |", block)
```

- [ ] **Step 2: Write the failing publication-contract assertions**

Require these report strings:

```python
required = (
    "我觉得在精不在多",
    "研究长名单不等于推荐",
    "商业产品硬门槛",
    "开源项目硬门槛",
    "同一个优秀产品可以覆盖多个场景",
    "当前没有足够证据的生产级开源推荐",
    "优先 PoC",
)
```

Also assert:

```python
self.assertNotIn("国内 27 个公开可识别对象", final_report)
self.assertNotIn("### 附录：全球市场地图", readme)
```

- [ ] **Step 3: Run the focused tests and verify red**

Run:

```bash
python3 -m unittest \
  tests.test_compiler.CompilerRenderingTests \
  tests.test_vertical_slice.PublicationDeliveryTests.test_repository_docs_describe_real_report_reproduction_and_limits \
  -v
```

Expected: failures because the compiler still renders the market map and the final report does not contain the curated-selection contract.

- [ ] **Step 4: Commit the failing contract**

```bash
git add tests/test_compiler.py tests/test_vertical_slice.py
git commit -m "Make publication tests reject product-list volume"
```

### Task 2: Stop rendering the discovery pool

**Files:**
- Modify: `tools/aris_geo/compiler.py`
- Modify: `README.md` through `python3 tools/compile_readme.py`
- Test: `tests/test_compiler.py`

**Interfaces:**
- Consumes: product profiles only for `_data_cutoff`.
- Produces: `render_compiled_block(...) -> str` containing the cutoff and internal-pool notice, independent of market-map length.

- [ ] **Step 1: Reduce the compiled block**

Implement:

```python
def render_compiled_block(
    profiles: Iterable[dict[str, Any]],
    market_map: Iterable[dict[str, Any]] | None = None,
) -> str:
    profile_list = list(profiles)
    return "\n".join(
        [
            f"> 数据截至 {_data_cutoff(profile_list)}",
            "> 完整候选池保留在 wiki/market-map.json，仅供研究与审计，不构成公开推荐。",
        ]
    )
```

Delete `_market_map_sort_key` and `_category_values`; keep `load_market_map` because build validation must continue detecting malformed research data.

- [ ] **Step 2: Rebuild README**

Run:

```bash
python3 tools/compile_readme.py
```

Expected: README compiled block contains no product table.

- [ ] **Step 3: Run compiler tests**

Run:

```bash
python3 -m unittest tests.test_compiler -v
```

Expected: all compiler tests pass.

- [ ] **Step 4: Commit**

```bash
git add tools/aris_geo/compiler.py README.md tests/test_compiler.py
git commit -m "Keep the discovery pool out of the public report"
```

### Task 3: Add a validated shortlist contract

**Files:**
- Create: `tools/aris_geo/shortlist.py`
- Create: `wiki/shortlist.json`
- Create: `tests/test_shortlist.py`

**Interfaces:**
- Consumes: `wiki/shortlist.json`, `wiki/products/*.json`.
- Produces: `validate_shortlist(payload: dict[str, Any], profile_slugs: set[str]) -> list[str]`.

- [ ] **Step 1: Write failing validator tests**

Create tests covering:

```python
def valid_payload():
    return {
        "schema_version": "v1",
        "max_unique": 8,
        "entries": [
            {
                "slug": "timus_geo",
                "name": "透镜GEO",
                "kind": "commercial",
                "status": "selected_poc",
                "scenarios": ["domestic_audit", "regulated"],
                "solves": "保存真实交互证据",
                "why_selected": ["中立账号", "完整录屏"],
                "evidence_basis": ["wiki/products/timus_geo.json#e1"],
                "limitations": ["逐端矩阵未公开"],
                "replacement_gap": "现有候选中少有完整录屏",
            }
        ],
    }
```

Assert that validation rejects:

- more than `max_unique` unique slugs;
- duplicate slugs;
- unknown profile slugs;
- invalid `kind` or `status`;
- empty scenarios, evidence, limitations, or replacement gap;
- `max_unique` above 8;
- an `open-source` entry with `selected_poc` status when its explicit gate record does not include `runnable_code`, `license`, `raw_results`, `reproducible_setup`, and `tests_or_benchmark`.

- [ ] **Step 2: Run tests and verify red**

Run:

```bash
python3 -m unittest tests.test_shortlist -v
```

Expected: import failure because `tools.aris_geo.shortlist` does not exist.

- [ ] **Step 3: Implement the validator**

Use constants:

```python
KINDS = frozenset({"commercial", "open-source", "research"})
STATUSES = frozenset({"selected_poc", "watch", "research_reference"})
OPEN_SOURCE_REQUIRED_GATES = frozenset(
    {"runnable_code", "license", "raw_results", "reproducible_setup", "tests_or_benchmark"}
)
```

Return human-readable validation errors rather than raising on the first error. Reject research entries with `selected_poc`; research is reference material, not a production recommendation.

- [ ] **Step 4: Add the reviewed seven-entry shortlist**

Write `wiki/shortlist.json` with seven unique entries:

```text
selected_poc:
  timus_geo   — domestic audit, B2B, regulated
  numseek     — SMB baseline, agency reporting
  baiyuan_geo — regulated, multi-brand, cross-border monitoring
  geoly_ai    — cross-border DTC and AI Shopping

watch:
  geolyze     — transparent diagnosis, ongoing scale/channel unknown
  aperture    — self-hosted API baseline, fails production open-source gate because project tests and repeat measurement are not evidenced

research_reference:
  geo_generative_engine_optimization — peer-reviewed benchmark and experiment reference, not a monitoring product
```

Every entry must include `solves`, `why_selected`, `evidence_basis`, `limitations`, and `replacement_gap`. The Aperture entry must include explicit gate booleans showing why it remains `watch`.

- [ ] **Step 5: Run validator tests**

Run:

```bash
python3 -m unittest tests.test_shortlist -v
```

Expected: all shortlist tests pass.

- [ ] **Step 6: Commit**

```bash
git add tools/aris_geo/shortlist.py wiki/shortlist.json tests/test_shortlist.py
git commit -m "Make shortlist admission explicit and auditable"
```

### Task 4: Rewrite the report around the small shortlist

**Files:**
- Modify: `docs/FINAL_REPORT.md`
- Modify: `README.md`
- Modify: `docs/METHODOLOGY.md`
- Test: `tests/test_vertical_slice.py`

**Interfaces:**
- Consumes: `wiki/shortlist.json`, existing product profiles, and `docs/research/AI_SEARCH_PIPELINE_SOURCES.md`.
- Produces: a conclusion-first public report with four selected PoC products, two watch candidates, and one research reference.

- [ ] **Step 1: Replace volume claims with the governing principle**

Open the report with the exact quotation from Global Constraints. State:

```text
研究长名单不等于推荐。
112 个对象只是发现池。
公开层只保留 7 个唯一对象，其中 4 个是优先 PoC，2 个值得观察，1 个是研究参考。
```

- [ ] **Step 2: Explain the root cause and selection gates**

Add compact sections:

```markdown
## 为什么以前筛不出好产品
## 精选方法
### 商业产品硬门槛
### 开源项目硬门槛
### 不足则不推荐
```

Explain that discoverability, marketing documentation, features, and stars cannot substitute for user value.

- [ ] **Step 3: Publish one scenario matrix with product reuse**

Use:

```markdown
| 场景 | 优先 PoC | 值得观察/空白 | 为什么 |
```

Allow `透镜GEO` to recur in domestic audit, B2B fact verification, and regulated evidence scenarios. Show no qualified recommendation for domestic mobile true-device monitoring and no production-grade open-source recommendation.

- [ ] **Step 4: Publish seven decision cards**

Each card must use:

```markdown
### Product — status
- 解决：
- 入选依据：
- 适合场景：
- 公开证据：
- 主要限制：
- 为什么没有被另一个候选替代：
```

Do not restore the 27-product directory or 112-product appendix.

- [ ] **Step 5: Preserve the high-value analysis**

Keep and tighten:

- GEO monitoring definition;
- six-stage observable pipeline;
- mobile/PC separation;
- data verification and conflicts of interest;
- fixed-question-set design;
- content × channel experiment;
- candidate→citation→mention→recommend funnel;
- procurement PoC and 90-day implementation.

Delete repeated vendor matrices, catalog-like directories, and any paragraph whose only purpose is demonstrating breadth.

- [ ] **Step 6: Update README and methodology**

README must lead with the governing principle and the seven-object public shortlist. Methodology must document:

- discovery pool versus recommendation layer;
- commercial/open-source gates;
- repeated product use across scenarios;
- the eight-unique-object ceiling;
- why no current open-source monitoring project received production recommendation.

- [ ] **Step 7: Run publication tests**

Run:

```bash
python3 -m unittest tests.test_vertical_slice -v
```

Expected: all publication tests pass.

- [ ] **Step 8: Commit**

```bash
git add docs/FINAL_REPORT.md README.md docs/METHODOLOGY.md tests/test_vertical_slice.py
git commit -m "Make the GEO report a curated decision guide"
```

### Task 5: Integrate shortlist validation into delivery gates

**Files:**
- Modify: `tests/test_vertical_slice.py`
- Modify: `tools/build_publication.py`
- Test: `tests/test_shortlist.py`
- Test: `tests/test_vertical_slice.py`

**Interfaces:**
- Consumes: `validate_shortlist`, generated product profiles.
- Produces: a publication build that fails when the reviewed shortlist references missing profiles or violates the eight-object ceiling.

- [ ] **Step 1: Write a failing integration test**

Add:

```python
def test_committed_shortlist_is_valid_and_references_profiles(self):
    payload = json.loads((REPO_ROOT / "wiki" / "shortlist.json").read_text())
    slugs = {path.stem for path in (REPO_ROOT / "wiki" / "products").glob("*.json")}
    self.assertEqual([], validate_shortlist(payload, slugs))
```

Add a build-helper test that passes an invalid shortlist path containing an unknown slug to
`validate_committed_shortlist(repo_root: Path, shortlist_path: Path) -> None` and expects
`ValueError` containing `unknown profile slug`.

- [ ] **Step 2: Run integration tests and verify red**

Run:

```bash
python3 -m unittest tests.test_shortlist tests.test_vertical_slice -v
```

Expected: failure because the publication builder does not validate the shortlist.

- [ ] **Step 3: Add validation to the publication build**

In `tools/build_publication.py`, define:

```python
def validate_committed_shortlist(repo_root: Path, shortlist_path: Path) -> None:
    payload = json.loads(shortlist_path.read_text(encoding="utf-8"))
    profile_slugs = {path.stem for path in (repo_root / "wiki" / "products").glob("*.json")}
    errors = validate_shortlist(payload, profile_slugs)
    if errors:
        raise ValueError("invalid shortlist:\n" + "\n".join(f"- {error}" for error in errors))
```

Call it from `main` after `build_publication`:

```python
validate_committed_shortlist(REPO_ROOT, REPO_ROOT / "wiki" / "shortlist.json")
```

Keep validation deterministic and offline.

- [ ] **Step 4: Run integration tests**

Run:

```bash
python3 -m unittest tests.test_shortlist tests.test_vertical_slice -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add tools/build_publication.py tests/test_shortlist.py tests/test_vertical_slice.py
git commit -m "Fail publication builds on invalid recommendations"
```

### Task 6: Rebuild and verify the final deliverable

**Files:**
- Verify all modified files.

**Interfaces:**
- Consumes: the complete repository.
- Produces: reproducible, committed final report and clean working tree.

- [ ] **Step 1: Rebuild**

Run:

```bash
python3 tools/build_publication.py
python3 tools/score.py
python3 tools/compile_readme.py
```

Expected: 19 profiles build and README stays free of the market table.

- [ ] **Step 2: Run all verification gates**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 tools/verify_evidence.py --strict
python3 tools/score.py --check
python3 tools/compile_readme.py --check
git diff --check
```

Expected: every command exits `0`.

- [ ] **Step 3: Check the public-surface constraints**

Run:

```bash
! rg -n "### 附录：全球市场地图|国内 27 个公开可识别对象" README.md docs/FINAL_REPORT.md
rg -n "我觉得在精不在多|当前没有足够证据的生产级开源推荐|同一个优秀产品可以覆盖多个场景" docs/FINAL_REPORT.md
```

Expected: the negative search finds nothing and all three governing statements are present.

- [ ] **Step 4: Commit final generated changes**

```bash
git add README.md docs/FINAL_REPORT.md docs/METHODOLOGY.md wiki/shortlist.json
git commit -m "Deliver the curated GEO product report"
```
