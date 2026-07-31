---
name: geo-review
description: Use when `/geo-review` runs as `vendor`, `skeptic`, or `arbiter` over a staged product folder and must emit only the review artifact visible in that persona's `--cwd`.
---

# Geo Review

Run one of the exact slash commands below and reason only from the files present in the current persona inbox.

## Commands

- `/geo-review --persona vendor --slug <slug>`
- `/geo-review --persona skeptic --slug <slug>`
- `/geo-review --persona arbiter --slug <slug>`

## Inputs

- `vendor only sees` the evidence bundle and current profile draft needed to defend sourced claims
- `skeptic only sees` the evidence bundle and current profile draft needed to challenge unsupported claims
- `arbiter sees` the evidence bundle plus `vendor.json` and `skeptic.json`
- [`skills/shared/SCHEMA.md`](../shared/SCHEMA.md)
- [`skills/shared/EVIDENCE_RULES.md`](../shared/EVIDENCE_RULES.md)
- [`skills/shared/GRADING.md`](../shared/GRADING.md)

## Outputs

- `vendor` writes `vendor.json`
- `skeptic` writes `skeptic.json`
- `arbiter` writes `patch.json` and any `unresolved` items needed by the driver

## Allowed observations

- `vendor` may defend only claims backed by visible evidence
- `skeptic` may attack missing sources, weak grades, unsupported wording, and hidden assumptions
- `arbiter` may resolve only from visible files, preferring patches over prose and preserving unknowns when evidence is insufficient

## Must not

- must not assume hidden files exist
- Do not network
- Do not calculate scores or `oss_health`
- Do not invent sources, observations, or persona messages not grounded in the visible files
- Do not let one persona speak for another; isolation is enforced by the filesystem, not by trust
