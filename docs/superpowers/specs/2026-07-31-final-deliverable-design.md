# ARIS-GEO Final Deliverable Design

## Goal

Replace the synthetic vertical-slice publication with a reproducible, evidence-backed
market report over a balanced set of real GEO/AEO products and projects.

## Acceptance criteria

1. `tools/geo_loop.py --live` wires every state-machine phase and can resume safely.
2. Network access exists only in the deterministic fetch phase. Model phases receive
   staged files and never receive credentials.
3. Tavily is optional. A checked-in source manifest with direct public URLs is a
   deterministic fallback; GitHub public endpoints may run anonymously within their
   published rate limit.
4. Each published non-unknown research leaf cites a locally hashed excerpt with URL,
   source kind, and retrieval date.
5. Vendor, skeptic, and arbiter reviews run in isolated inboxes. Python validates and
   applies the arbiter patch through a strict field allowlist.
6. Python alone computes grades, scores, risk flags, OSS health, and README tables.
7. The final report contains only real products. Synthetic fixtures remain under
   `tests/fixtures/` and are clearly excluded from publication.
8. The full test suite, strict evidence gate, score gate, README byte-for-byte gate,
   freshness check, syntax compilation, and fault-injection checks pass.

## Delivery set

The default publication target is 12–15 products, balanced across overseas SaaS,
domestic China products, open-source tools, academic/reference implementations, and
skill/prompt packs. A product may publish with unknown fields when public evidence is
absent; absence is never converted into a negative factual claim.

## Failure policy

- A failed fetch, invalid model artifact, denied tool, excessive ARIS iteration count,
  or gate failure leaves a resumable state record and returns a non-zero process code.
- Missing optional credentials cause an explicit capability downgrade, not fabricated
  search coverage.
- Products that cannot meet the evidence contract are excluded from the compiled report
  and named in the run summary.

## Publication boundary

The repository contains source manifests, short attributed excerpts, hashes, generated
profiles, review artifacts, audit records, and the compiled report. It never contains
API keys, cookies, full copyrighted pages, or the temporary ARIS binary.
