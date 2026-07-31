---
name: geo-profile
description: Use when `/geo-profile` must turn the visible evidence digest into `wiki/products/<slug>.json` while leaving all computed fields to Python.
---

# Geo Profile

Run `/geo-profile` after `evidence.md` exists and before any review persona starts.

## Inputs

- `wiki/raw/<slug>/evidence.md`
- [`skills/shared/SCHEMA.md`](../shared/SCHEMA.md)
- [`skills/shared/EVIDENCE_RULES.md`](../shared/EVIDENCE_RULES.md)
- [`skills/shared/GRADING.md`](../shared/GRADING.md)

## Outputs

- `wiki/products/<slug>.json`
- Fill research-backed envelopes and `unknowns[]`; leave computed fields absent

## Allowed observations

- Use `conf: "unknown"` with `v: null` when the evidence bundle does not support a claim
- Add `note` only for `conf: "inferred"`
- Propose `effect_claims[*].grade_final` from the visible evidence, knowing Python will recompute it later

## Must not

- Do not request, read, use, write, or echo any API key, token, secret, password, or credential.
- Do not network
- Do not calculate `scores`, `risk_flags`, `oss_health`, or `audit`
- Do not invent evidence ids or write unsupported fields
- Do not fill a non-unknown envelope without `src`
