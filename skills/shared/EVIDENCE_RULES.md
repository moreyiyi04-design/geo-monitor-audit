# Evidence Rules

- Every cited source id must resolve to an item in `evidence[]`.
- Every evidence record carries `url`, `kind`, `fetched_at`, `sha256`, `excerpt_path`, and `paid_placement_suspected`.
- `fetched_at` is an ISO date captured by Python during fetch.
- `sha256` matches the excerpt bytes on disk; model phases must never rewrite hashes.
- `paid_placement_suspected` stays explicit because suspected advertorial content cannot silently count as clean independent evidence.
- When evidence does not support a field, leave it `unknown` instead of guessing.
