# GEO Monitoring Decision Report Redesign

## Goal

Replace the current catalog-like publication with a conclusion-first decision
report that a reader can use to understand GEO monitoring, shortlist domestic
vendors, validate data, control conflicts of interest, and build a
monitoring-driven optimization program.

The report must answer these questions without requiring the reader to inspect
JSON profiles or infer meaning from raw scores:

1. What is GEO monitoring?
2. Which domestic GEO monitoring platforms exist?
3. How do they differ, and which enterprise types fit each capability pattern?
4. Which products publicly disclose mobile and PC coverage?
5. How can monitoring data be verified?
6. Which free diagnostics, free plans, and trials exist?
7. Can the same party credibly monitor and optimize?
8. How does monitoring drive optimization, and how should a fixed question set
   be built?

## Chosen approach

Use one definitive report, `docs/FINAL_REPORT.md`, as the primary deliverable.
`README.md` becomes a compact project and executive entry point. Machine-generated
market data remains available as an appendix, but raw score tables and risk-label
lists no longer occupy the main reading path.

This is preferred over adding a FAQ to the existing report because the problem is
structural: the existing publication starts from product records rather than a
model of how AI search works and how a buyer makes a decision.

## Analysis model

The report uses a six-stage observable funnel:

1. **Environment and channel** — model, version, account, region, device,
   search/reasoning switches.
2. **Crawl, indexing, and content supply** — whether a document can enter an
   engine's searchable corpus.
3. **Query understanding and retrieval** — query decomposition, query fan-out,
   candidate retrieval, and source eligibility.
4. **Reranking and evidence selection** — which documents and passages survive
   relevance, authority, freshness, diversity, safety, and extractability filters.
5. **Answer synthesis and recommendation** — which evidence is cited, which
   entities are mentioned, and which brands are recommended.
6. **Terminal rendering and action** — citation UI, product cards, local results,
   links, and downstream conversion.

The exact internals of consumer AI engines are not public. Every statement about
this funnel is classified as:

- documented mechanism;
- observable inference;
- hypothesis requiring a reproducible experiment.

The reported “approximately 5 × 6 candidate results” observation for 豆包 is
treated as a hypothesis and experiment target, not as a platform fact.

## Breaking the post-hoc analytics ceiling

Simple monitoring sees only the final answer and therefore tends to recommend
copying highly cited content or publishing on highly cited domains. The redesigned
report evaluates whether a tool can observe or experimentally probe intermediate
stages:

- query rewrites or fan-out;
- retrieved candidate documents;
- document- and passage-level provenance;
- candidate-to-citation and citation-to-mention conversion;
- repeated-sample variance;
- controlled content and distribution interventions;
- propagation lag and change-point attribution;
- channel-specific terminal rendering.

No vendor is credited with observing an internal stage merely because it publishes
a score or uses the word “AI”. Publicly undisclosed capabilities remain unknown.

## Report structure

1. Executive conclusions and a five-minute decision summary.
2. Definition: what GEO monitoring is and is not.
3. The six-stage AI-search funnel and failure diagnosis.
4. Direct answers to the eight buyer questions.
5. Domestic vendor landscape and capability matrix.
6. Mobile/PC/channel coverage matrix.
7. Free tool, free plan, trial, and paid-entry matrix.
8. Evidence verification and conflict-of-interest framework.
9. Fixed-question-set design.
10. Monitoring-driven optimization and causal experiment loop.
11. Who can break the ceiling: capability gap analysis by vendor archetype.
12. Procurement scorecard and 30/60/90-day implementation plan.
13. Evidence and global-market appendices.

## Cleanup scope

The cleanup is limited to the report publication surface:

- delete the rendered risk-label list;
- delete raw score and redundant profile tables from the README;
- keep `risk_flags` and computed scores in structured JSON for audit and
  regression compatibility;
- retain one machine-generated global market appendix;
- remove repeated introductory copy and route readers to one definitive report.

No scoring engine, evidence envelope, source hash, or product profile is removed.

## Evidence and trust rules

- Vendor pages support only vendor-stated product capabilities.
- A vendor-owned monitoring tool is not automatically invalid, but it has a
  conflict of interest when the same party sells optimization.
- Trust requires raw-answer access, fixed and versioned questions, disclosed
  channel settings, repeat sampling, timestamped evidence, formula disclosure,
  change logs, and independent spot checks.
- Free diagnostic, free recurring plan, and time-limited trial are reported as
  separate commercial categories.
- “Supports an engine” never implies support for every web, desktop, App,
  mini-program, and API surface.

## Acceptance criteria

- The first report section gives explicit conclusions.
- All eight buyer questions receive direct answers.
- The six-stage funnel maps failures to observations, interventions, and tests.
- The report explicitly answers who can and cannot break the post-hoc ceiling.
- The domestic comparison includes capability, channel, price-entry,
  independence, evidence, best-fit, and limitations.
- The report includes a versioned fixed-question-set template and an experiment
  loop.
- `README.md` contains no rendered `标签清单`, raw score table, or redundant
  deep-profile table.
- The evidence builder, score checker, report compiler, and complete test suite
  remain reproducible.
