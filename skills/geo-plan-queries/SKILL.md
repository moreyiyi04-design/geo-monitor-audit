---
name: geo-plan-queries
description: Use when the driver needs `/geo-plan-queries` to turn the visible product context into an offline `queries.json` search plan without fetching anything.
---

# Geo Plan Queries

Run `/geo-plan-queries` after the slug is known and before Python performs the only networked fetch phase.

## Inputs

- The visible slug context in the current `--cwd`
- [`skills/shared/SCHEMA.md`](../shared/SCHEMA.md)
- [`skills/shared/EVIDENCE_RULES.md`](../shared/EVIDENCE_RULES.md)

## Outputs

- `queries.json`
- Query strings plus brief intent labels if the driver asks for them

## Allowed observations

- Cover homepage, pricing, methodology, case studies, and public repo angles only when those angles matter for the schema
- Prefer query variants that can surface first-party, registry, academic, and independent third-party evidence
- Keep the plan deterministic and concise; this phase chooses what to search, not what is true

## Must not

- Do not request, read, use, write, or echo any API key, token, secret, password, or credential.
- Do not network
- Do not digest fetched pages into conclusions
- Do not calculate scores or write computed fields
- Do not invent candidate evidence or source kinds
