# China GEO Market Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current global-heavy report into a domestic-first GEO vendor selection deliverable.

**Architecture:** Keep the existing two-layer data model: identity-level breadth in `wiki/market-map.json` and evidence-gated facts in `wiki/catalog.json`. Add a dedicated domestic analysis document for channel and brand-fit judgments, then regenerate all derived profiles and README tables.

**Tech Stack:** Python 3.11+, JSON, Markdown, unittest

## Global Constraints

- No new dependencies.
- Official vendor statements remain first-party evidence, not validated outcomes.
- Platform coverage must not be presented as proof of web, desktop, mobile, mini-program, or API coverage.
- Unknown public details remain unknown.
- Recommendations are conditional capability fits, not a total ranking.

---

### Task 1: Lock the domestic-first publication contract

**Files:**
- Modify: `tests/test_vertical_slice.py`

- [ ] Require at least 27 domestic market-map entries and the 透镜GEO slug.
- [ ] Require 19 deep profiles and five new domestic profile slugs.
- [ ] Require domestic analysis sections for channels, capabilities, and brand fit.
- [ ] Run the focused test and confirm it fails because the new publication is absent.

### Task 2: Expand domestic market and evidence data

**Files:**
- Modify: `wiki/market-map.json`
- Modify: `wiki/catalog.json`

- [ ] Add official identity-level entries for the newly verified domestic products.
- [ ] Add source extracts and bounded facts for the five representative profiles.
- [ ] Keep channel facts unknown when public pages disclose engines but not surfaces.
- [ ] Regenerate profiles, raw evidence, queue, and source index.

### Task 3: Publish the domestic analysis

**Files:**
- Create: `docs/CHINA_MARKET.md`
- Modify: `README.md`
- Modify: `docs/METHODOLOGY.md`

- [ ] Put the domestic executive summary and vendor landscape before overseas references.
- [ ] Publish the mobile/PC/channel matrix and comparability controls.
- [ ] Publish capability differences and conditional brand-fit recommendations.
- [ ] Add the 透镜GEO deep dive with explicit supported and undisclosed claims.
- [ ] Update publication counts and scope language.

### Task 4: Rebuild and verify

**Files:**
- Generated: `wiki/products/*.json`
- Generated: `wiki/raw/*`
- Generated: `wiki/queue.json`
- Generated: `wiki/sources.json`
- Generated section: `README.md`

- [ ] Run the publication builder, scorer, and README compiler.
- [ ] Run all unit tests.
- [ ] Run strict evidence verification, score check, and README check.
- [ ] Review the final diff for unsupported claims and stale counts.
