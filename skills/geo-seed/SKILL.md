---
name: geo-seed
description: Use when the driver needs `/geo-seed` to turn staged candidate notes into `wiki/queue.json` without browsing, scoring, or filling computed fields.
---

# Geo Seed

Run `/geo-seed` in a staging directory that already contains the candidate notes the driver wants normalized into queue entries.

## Inputs

- Plain-text candidate notes already visible in the current `--cwd`
- [`skills/shared/SCHEMA.md`](../shared/SCHEMA.md) for slug style and fields the later phases expect

## Outputs

- `wiki/queue.json`
- Stable slugs only; no hidden scratch state

## Allowed observations

- Normalize product names into deterministic slugs
- Keep only entries that are visibly GEO-related in the provided notes
- Preserve uncertainty by omitting or marking unknown rather than inventing detail

## Must not

- Do not request, read, use, write, or echo any API key, token, secret, password, or credential.
- Do not network
- Do not calculate scores, grades, or `oss_health`
- Do not invent sources, URLs, or fetched dates
- Do not write computed fields such as `scores`, `risk_flags`, or `audit`
