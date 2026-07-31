# Comprehensive GEO Market Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish a broad GEO/AEO market map without weakening the evidence standard of the existing deep profiles.

**Architecture:** Keep identity-level market discovery in `wiki/market-map.json` and evidence-backed research in `wiki/catalog.json`. Extend the deterministic README compiler to render both layers and reject inconsistent map data.

**Tech Stack:** Python 3.11+, JSON, unittest, Markdown

## Global Constraints

- No new dependencies.
- `market-map-only` entries never receive deep scores.
- Every `deep-profile` map slug must match a committed product profile.
- The report must state that the inventory is a dated discovery snapshot, not a universal registry.

---

### Task 1: Market map dataset

**Files:**
- Create: `wiki/market-map.json`

- [x] Collect official product and repository URLs across all in-scope categories.
- [x] Classify every row by market, category, delivery form, openness, and coverage.
- [x] Keep ambiguous service-only and generic infrastructure entries out of the included set.

### Task 2: Deterministic compilation

**Files:**
- Modify: `tools/aris_geo/compiler.py`
- Modify: `tests/test_compiler.py`
- Modify: `tests/test_vertical_slice.py`

- [ ] Write failing tests for map rendering and invalid data.
- [ ] Implement loading, validation, and deterministic rendering.
- [ ] Verify that compilation still works when a fixture has no market map.

### Task 3: Publication copy

**Files:**
- Modify: `README.md`
- Modify: `docs/METHODOLOGY.md`

- [ ] Replace the 14-object market claim with separate map and deep-profile counts.
- [ ] Explain inclusion, exclusion, and coverage-level semantics.
- [ ] Recompile the README and run all deterministic gates.
