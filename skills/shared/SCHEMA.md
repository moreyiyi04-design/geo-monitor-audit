# Schema Contract

- Every research-derived leaf is an envelope: `{"v": ..., "src": [...], "conf": "stated|inferred|unknown"}`.
- `conf: "unknown"` requires `v: null` and an empty `src`.
- `conf: "inferred"` requires a non-empty `note`.
- `unknowns[]` must list every unknown envelope path and only unknown envelope paths.
- Model-written output may fill research fields and `effect_claims[*].grade_final`, but Python recomputes and checks them.
- Model phases must not write computed fields: `scores`, `risk_flags`, `oss_health`, or `audit`.
