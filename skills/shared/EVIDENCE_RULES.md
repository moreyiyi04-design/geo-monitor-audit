# Evidence Rules

- Every evidence record needs an `id`; all cited source ids must resolve to an item in `evidence[]`.
- Every cited source id must resolve to an item in `evidence[]`.
- Every evidence record carries `url`, `kind`, `fetched_at`, `sha256`, `excerpt_path`, and `paid_placement_suspected`.
- Exact `kind` enum:
  `regulatory_authoritative`, `academic`, `methodology_doc`, `third_party_dataset`, `third_party_report`, `registry`, `repo`, `vendor_doc`, `vendor_pricing_page`, `vendor_marketing`, `community`
- `fetched_at` is an ISO date captured by Python during fetch.
- `sha256` matches the excerpt bytes on disk; model phases must never rewrite hashes.
- `paid_placement_suspected` stays explicit because suspected advertorial content cannot silently count as clean independent evidence.
- When evidence does not support a field, leave it `unknown` instead of guessing.
