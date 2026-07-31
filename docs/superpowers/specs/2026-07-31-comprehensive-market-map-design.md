# Comprehensive GEO Market Map Design

## Goal

Replace the misleading impression that the 14 deep profiles are the whole GEO
market with a two-layer publication:

1. a broad market map containing every identifiable product found in the current
   discovery pass; and
2. the existing evidence-gated deep profiles for products with enough public
   material to support field-level scoring.

## Scope

The market map includes dedicated GEO/AEO platforms, AI-search modules inside
established SEO suites, domestic China products, self-hosted trackers, agent
skills, and academic benchmarks. Consultancies without a distinct product,
generic web-scraping infrastructure, dead domains, and products that only
mention AI without an AI-search use case are excluded.

Each market-map row contains only identity and classification fields that can be
checked from a public product or repository page. A `market-map-only` row must
not receive deep scores. A `deep-profile` row must have a matching structured
profile under `wiki/products/`.

## Publication

`wiki/market-map.json` is the broad inventory. The README compiler renders it
before the deep-profile matrices and labels coverage explicitly. The existing
catalog remains the source of truth for evidence excerpts, grades, risk flags,
and deterministic scores.

## Acceptance

- The map contains at least 60 unique products.
- All 14 deep profiles appear in the map with `coverage: deep-profile`.
- Duplicate slugs and invalid coverage values fail compilation.
- The README clearly distinguishes mapped products from deeply evaluated ones.
- The report publishes exclusions and coverage limitations rather than claiming
  market exhaustiveness.
