---
name: geo-digest
description: Use when `/geo-digest` must turn already-fetched raw excerpts into `evidence.md` without adding facts beyond the visible files.
---

# Geo Digest

Run `/geo-digest` only after Python has already fetched and hashed the excerpts for one slug.

## Inputs

- `wiki/raw/<slug>/*.txt`
- Visible excerpt metadata such as URL, `kind`, `fetched_at`, and `sha256`
- [`skills/shared/EVIDENCE_RULES.md`](../shared/EVIDENCE_RULES.md)

## Outputs

- `wiki/raw/<slug>/evidence.md`
- One evidence section per visible evidence id

## Allowed observations

- Summarize only what the excerpt directly states or clearly supports
- Carry forward uncertainty and contradictory evidence
- Note whether a source looks first-party, registry, academic, or third-party according to the supplied metadata

## Must not

- Do not network
- Do not invent evidence ids, URLs, source kinds, or hashes
- Do not calculate grades or scores
- Do not write `scores`, `risk_flags`, `oss_health`, or `audit`
