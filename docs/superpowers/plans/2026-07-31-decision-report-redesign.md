# GEO Monitoring Decision Report Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a conclusion-first GEO monitoring decision report that answers buyer questions, explains the observable AI-search pipeline, and turns monitoring into controlled optimization experiments.

**Architecture:** `docs/FINAL_REPORT.md` is the single definitive report; `README.md` is a compact executive and reproducibility entry point. The compiler retains one machine-generated global market appendix while structured profiles keep scores and risk flags for audit without rendering noisy tables.

**Tech Stack:** Python 3.11+, JSON, Markdown, unittest

## Global Constraints

- No new dependencies.
- Engine internals are opaque, so documented mechanisms, observable inferences, and hypotheses must remain separate.
- Vendor pages prove vendor-stated capabilities, not independent outcomes.
- Platform coverage never implies web, desktop, App, mini-program, and API coverage.
- Free diagnostic, recurring free plan, and time-limited trial are separate categories.
- Computed scores and risk flags remain in JSON even when removed from the rendered report.

---

### Task 1: Lock the streamlined publication surface

**Files:**
- Modify: `tests/test_compiler.py`
- Modify: `tests/test_vertical_slice.py`

**Interfaces:**
- Consumes: `render_compiled_block(profiles, market_map)` from `tools.aris_geo.compiler`.
- Produces: a compiled appendix containing `### 附录：全球市场地图` and no raw score, profile, or risk-label sections.

- [ ] **Step 1: Replace compiler expectations with the decision-report contract**

Add assertions equivalent to:

```python
block = render_compiled_block([profile], market_map)
self.assertIn("### 附录：全球市场地图", block)
self.assertNotIn("### 选型矩阵", block)
self.assertNotIn("### 分数", block)
self.assertNotIn("### 产品档案表", block)
self.assertNotIn("### 标签清单", block)
```

Update the repository delivery test to require `docs/FINAL_REPORT.md` and these
exact section headings:

```python
required = (
    "## 一页结论",
    "## 什么是GEO监测",
    "## AI搜索的六阶段可观测链路",
    "## 八个采购问题的直接答案",
    "## 国内GEO监测平台比较",
    "## 数据可信度与利益冲突",
    "## 固定问题集如何建立",
    "## 从监测到优化实验",
    "## 谁能突破事后统计的天花板",
)
```

- [ ] **Step 2: Run the focused tests and verify red**

Run:

```bash
python3 -m unittest \
  tests.test_compiler.CompilerRenderingTests \
  tests.test_vertical_slice.PublicationDeliveryTests.test_repository_docs_describe_real_report_reproduction_and_limits \
  -v
```

Expected: failures because the compiler still renders `标签清单` and
`docs/FINAL_REPORT.md` does not exist.

### Task 2: Delete low-signal rendered tables

**Files:**
- Modify: `tools/aris_geo/compiler.py`
- Modify: `README.md` through `python3 tools/compile_readme.py`

**Interfaces:**
- Consumes: market-map entries from `wiki/market-map.json`.
- Produces: only the dated global market appendix in the compiled block.

- [ ] **Step 1: Reduce `render_compiled_block` to the global appendix**

Keep the data cutoff, evidence boundary line, market-map heading/table, sorting,
and validation. Delete rendering loops for:

```text
### 选型矩阵
### 分数
### 产品档案表
### 标签清单
```

Delete compiler-only helpers that become unused:

```text
_profile_sort_key
_display_name
_primary_category
_category_list
_pricing_label
_score_value
_sorted_flags
_tier_rank
_flag_prefix
```

Keep `_field_value` and `_unwrap` only if another compiler path still uses them;
otherwise delete them after confirming with `rg`.

- [ ] **Step 2: Recompile and run focused tests**

Run:

```bash
python3 tools/compile_readme.py
python3 -m unittest tests.test_compiler -v
```

Expected: compiler tests pass and README contains no `### 标签清单`.

### Task 3: Research the AI-search pipeline with primary sources

**Files:**
- Create: `docs/research/AI_SEARCH_PIPELINE_SOURCES.md`

**Interfaces:**
- Consumes: official documentation and primary research.
- Produces: a concise source ledger separating documented mechanisms, inferences,
  and hypotheses for `docs/FINAL_REPORT.md`.

- [ ] **Step 1: Capture primary evidence for crawl, index, retrieval, and ranking**

Record official sources supporting:

- crawl/index/serve separation;
- query rewriting or fan-out;
- candidate retrieval and semantic reranking;
- grounding/citation metadata;
- consumer channel differences where officially disclosed.

For each source, write:

```markdown
### Source name
- URL:
- Supports:
- Does not prove:
- Classification: documented mechanism | reference architecture
```

- [ ] **Step 2: Record opaque domestic-engine hypotheses**

Create a hypothesis table with these columns:

```markdown
| Hypothesis | Observable signal | Reproduction method | Falsification condition |
```

Include the proposed 豆包 “approximately 5 × 6 candidates” observation and state
that no public source currently establishes it as an internal platform constant.

### Task 4: Write the definitive decision report

**Files:**
- Create: `docs/FINAL_REPORT.md`
- Delete: `docs/CHINA_MARKET.md`

**Interfaces:**
- Consumes: `wiki/market-map.json`, `wiki/catalog.json`,
  `docs/research/AI_SEARCH_PIPELINE_SOURCES.md`, and official vendor sources.
- Produces: the final reader-facing research report.

- [ ] **Step 1: Write the conclusion and definitions**

The opening must answer, before methodology:

- what buyers should conclude;
- what no vendor has publicly proven;
- which capability patterns fit which enterprise types;
- why mobile and PC require separate samples;
- why monitoring alone does not answer “what to write and where to publish”.

Define GEO monitoring as repeated, controlled observation of AI answers, citations,
recommendations, and terminal presentation. Explicitly exclude rank guarantees,
one-off manual screenshots, and content generation without measurement.

- [ ] **Step 2: Write the six-stage failure-diagnosis framework**

For every stage, include:

```markdown
| Stage | Buyer question | Observable data | Failure signal | Intervention | Verification |
```

The stages are environment/channel; crawl/index; query/retrieval; reranking/evidence
selection; synthesis/recommendation; terminal/action.

- [ ] **Step 3: Answer the eight buyer questions directly**

Use an answer-first table covering cognition, procurement, comparison, capability,
trust, price, risk, and implementation. Each answer must link to the detailed
section that follows.

- [ ] **Step 4: Publish useful domestic comparison matrices**

The core-vendor table must include:

```markdown
| Vendor | Product type | Evidence return | PC/web | Mobile App | Free entry | Monitor/optimize relationship | Best fit | Main limitation |
```

Use `已披露`, `部分披露`, or `未公开`; never infer channel support from platform
logos. Separate the complete 27-product directory from the evidence-backed
comparison of eight deep profiles.

- [ ] **Step 5: Write trust and conflict-of-interest controls**

Define four operating models:

1. independent monitor + client optimization;
2. monitor vendor + separate optimization provider;
3. one vendor with raw evidence and controlled acceptance;
4. self-owned monitor that self-certifies results without raw evidence.

Explain that model 4 is unacceptable for outcome-based payment, while model 3
requires fixed questions, raw responses, timestamped evidence, disclosed formulas,
holdout prompts, and independent spot checks.

- [ ] **Step 6: Write fixed-question and experiment protocols**

Publish a concrete panel:

```text
70% fixed core questions
20% rotating category/competitor questions
10% emerging-event questions
3-5 repeats per prompt/channel/time window
separate Web/PC and mobile denominators
version every wording or configuration change
```

Publish the experiment record:

```markdown
| Hypothesis | Changed unit | Target prompts | Holdout prompts | Channel | Expected lag | Success criterion | Stop condition |
```

- [ ] **Step 7: Answer who can break the ceiling**

State the market conclusion explicitly:

- no public evidence shows a vendor can inspect the complete internal retrieval
  and generation pipeline of domestic consumer engines;
- outcome-only dashboards and simple open-source trackers cannot break the ceiling;
- the closest tools are those that retain source/process evidence and support
  controlled interventions, but their public evidence still covers only parts of
  the chain;
- the real ceiling-breaker is a measurement and experimentation system combining
  query/candidate telemetry, passage provenance, repeated samples, deployments,
  holdouts, lag modeling, and change attribution.

Evaluate 透镜GEO, 百原GEO, GEOly, and representative open-source trackers against
those capabilities without claiming undisclosed internals.

### Task 5: Make README the executive entry point

**Files:**
- Modify: `README.md`
- Modify: `docs/METHODOLOGY.md`
- Modify: `tests/test_vertical_slice.py`

**Interfaces:**
- Consumes: the definitive report and compiled global appendix.
- Produces: a compact entry point that links to `docs/FINAL_REPORT.md`.

- [ ] **Step 1: Replace the handwritten README introduction**

Keep:

- five conclusion bullets;
- one prominent final-report link;
- reproducibility commands;
- evidence boundary;
- optional live orchestration and security notes.

Delete repeated vendor analysis already in the final report and references to
`docs/CHINA_MARKET.md`.

- [ ] **Step 2: Update methodology and delivery tests**

Document the six-stage model, the three claim classifications, and the removal of
rendered labels from the reader-facing report while retaining computed JSON audit
data.

Run:

```bash
python3 tools/compile_readme.py
python3 -m unittest tests.test_vertical_slice -v
```

Expected: all delivery tests pass.

### Task 6: Verify the complete deliverable

**Files:**
- Verify all changed files.

**Interfaces:**
- Consumes: final repository state.
- Produces: completion evidence.

- [ ] **Step 1: Run all deterministic gates**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 tools/verify_evidence.py --strict
python3 tools/score.py --check
python3 tools/compile_readme.py --check
git diff --check
```

Expected: 0 failures and exit code 0 for every command.

- [ ] **Step 2: Run content acceptance checks**

Run:

```bash
rg -n "## 一页结论|## 什么是GEO监测|## AI搜索的六阶段可观测链路|## 八个采购问题的直接答案|## 数据可信度与利益冲突|## 固定问题集如何建立|## 从监测到优化实验|## 谁能突破事后统计的天花板" docs/FINAL_REPORT.md
! rg -n "### 标签清单|### 分数|### 产品档案表" README.md
```

Expected: every final-report section is present and no deleted rendered section
appears in README.
