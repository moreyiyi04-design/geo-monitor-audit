# China GEO Market Expansion Design

## Goal

Rebalance the final deliverable around the domestic China GEO market and make it
usable for vendor selection. The report must answer four questions directly:

1. Which domestic GEO products are publicly identifiable?
2. What does the public evidence support for representative domestic products,
   including 透镜GEO?
3. Why can mobile-app, desktop/web, mini-program, and API observations differ?
4. Which capability pattern fits each brand type?

## Publication structure

`docs/CHINA_MARKET.md` becomes the primary domestic analysis. It contains the
domestic landscape, representative-vendor evidence table, a 透镜GEO deep dive,
channel methodology, capability differences, brand-fit recommendations, and a
procurement checklist. `README.md` links to this analysis before the broad global
market map and summarizes its conclusions.

The global market map remains the breadth layer. It is expanded with verified
domestic product identities. Five representative domestic products are promoted
to evidence-gated profiles through `wiki/catalog.json`; all other additions remain
`market-map-only`.

## Channel model

The report treats an AI engine and an access channel as separate variables.
“Supports 豆包” does not prove coverage of every 豆包 surface. The minimum channel
matrix is:

- browser/web;
- desktop client;
- iOS app;
- Android app;
- mini-program or ecosystem entry;
- API.

Comparable samples must also hold login state, region, location permission,
search/reasoning toggle, model/version, session reset, repeat count, and timestamp
constant. Publicly undisclosed channel coverage is reported as undisclosed, never
inferred from a platform logo.

## Vendor evidence

Deep-profile facts use official vendor pages and retain the existing
`stated | inferred | unknown` evidence contract. Vendor-authored performance
numbers do not become independent evidence. Public identity/classification is
enough for market-map inclusion but not for scoring.

Representative domestic profiles:

- 透镜GEO;
- 南云GEO;
- GEO可见度诊断;
- 百原GEO;
- GEOly.

They were selected to represent auditable monitoring, self-service monitoring,
transparent diagnosis, China/global multi-platform operations, and DTC/e-commerce
specialization.

## Brand-fit framework

Recommendations are made by capability pattern, not by a universal ranking:

- consumer/local/lifestyle brands;
- B2B, industrial, and professional services;
- e-commerce and DTC;
- regulated industries;
- multi-brand groups and agencies;
- cross-border brands;
- early-stage and small businesses.

Every recommendation states the required evidence and the conditions under which
the fit changes.

## Acceptance

- The market map contains at least 27 domestic entries and includes 透镜GEO.
- The publication has at least 19 deep profiles, including the five new domestic
  representatives.
- The domestic analysis distinguishes platform coverage from channel coverage.
- Mobile/PC differences, capability layers, and brand-fit recommendations are
  explicit.
- README and methodology no longer describe domestic fit as a known unaddressed
  limitation.
- The deterministic publication, evidence, score, and README checks pass.
