# Task 2 Report: Claim Grading and Deterministic Scores

## Scope

Implemented deterministic grading and scoring for the Task 2 slice:

- `tools/aris_geo/grading.py`
- `tools/aris_geo/scoring.py`
- `tools/noise_floor.json`
- `tests/test_grading.py`
- `tests/test_scoring.py`
- `tools/aris_geo/__init__.py`

## RED

Added focused tests first, then ran:

```bash
python3 -m unittest tests.test_grading tests.test_scoring -v
```

Observed expected missing-implementation failure:

```text
ModuleNotFoundError: No module named 'tools.aris_geo.grading'
ModuleNotFoundError: No module named 'tools.aris_geo.scoring'
```

This satisfied the TDD red step before any production code existed.

## GREEN

Implemented:

- `final_grade(claim, evidence, vendor_domains, noise_floors)`
- `calculate_scores(profile)`
- `derive_auto_risk_flags(profile)`
- default noise-floor data in `tools/noise_floor.json`
- package exports in `tools/aris_geo/__init__.py`

Focused rerun:

```bash
python3 -m unittest tests.test_grading tests.test_scoring -v
```

Result:

```text
Ran 11 tests in 0.002s
OK
```

## Full Verification

Full suite:

```bash
python3 -m unittest discover -s tests -v
```

Result:

```text
Ran 21 tests in 0.016s
OK
```

Static syntax check:

```bash
python3 -m py_compile \
  tools/aris_geo/grading.py \
  tools/aris_geo/scoring.py \
  tools/aris_geo/__init__.py \
  tests/test_grading.py \
  tests/test_scoring.py
```

Result: success, no output.

## What Changed

- Added deterministic A-E grading with:
  - independent-source A/B qualification
  - vendor-domain downgrades
  - suspected-paid-placement downgrade for B-grade reports
  - explicit `claimed_change_pp` noise-floor downgrade contract
- Added deterministic score recomputation for:
  - `transparency`
  - `verifiability`
  - `lock_in_risk`
  - `measurement_rigor`
  - category-sensitive `oss_health`
- Added automatic risk flags for measurement, pricing, evidence quality, and OSS hygiene signals described in `docs/DESIGN.md` sections 6.3-6.5 and 11.
- Added regression tests covering:
  - A-E mechanics
  - vendor-hosted downgrade behavior
  - suspected-placement downgrade behavior
  - below/equal/above/absent/invalid noise-floor inputs
  - all five score dimensions
  - deterministic automatic labels

## Self-Review

- Scope stayed inside the assigned files.
- No input mutation is performed by grading or scoring.
- The noise-floor contract is documented in `grading.py` and encoded in `tools/noise_floor.json`.
- `calculate_scores()` recomputes verifiability from deterministic grading rather than trusting stored `grade_final`.

## Concerns / Notes

- The schema does not define a separate “public methodology” envelope, so `transparency` treats the presence of `methodology_doc` evidence as the deterministic proxy for that score point.
- The D/E-majority auto label is triggered when `verifiability < 2` or when more than half of claims deterministically resolve to D/E, which keeps the label aligned with the wording in section 11 for mixed-claim profiles.

## Fix Round 1

### RED

Added focused regressions for:

- unknown-engine numeric `D` claims must not emit the noise-floor flag
- vendor-hosted A/B candidate downgrades must emit a claim-level auto flag
- suspected-paid-placement B downgrades must emit a claim-level auto flag
- `tactics.poisoning_fingerprints` must emit the documented orange label at 3 distinct non-empty hits

Red run:

```bash
python3 -m unittest tests.test_scoring -v
```

Observed expected failures against the previous implementation:

```text
FAIL: test_derive_auto_risk_flags_does_not_mark_unknown_engine_d_claim_as_noise_floor
ERROR: test_derive_auto_risk_flags_emits_claim_level_flag_for_vendor_hosted_ab_downgrades
ERROR: test_derive_auto_risk_flags_emits_claim_level_flag_for_suspected_paid_placement_downgrades
ERROR: test_derive_auto_risk_flags_emits_poisoning_fingerprint_label_at_three_distinct_hits
```

### GREEN

Implemented a shared deterministic claim assessment path in `grading.py` and
made `derive_auto_risk_flags()` consume downgrade reasons instead of inferring
them from the final grade alone.

Focused rerun:

```bash
python3 -m unittest tests.test_grading tests.test_scoring -v
```

Result:

```text
Ran 15 tests in 0.005s
OK
```

Full suite rerun:

```bash
python3 -m unittest discover -s tests -v
```

Result:

```text
Ran 25 tests in 0.015s
OK
```

Syntax check:

```bash
python3 -m py_compile tools/aris_geo/grading.py tools/aris_geo/scoring.py tests/test_scoring.py
```

Result: success, no output.

### Fix-Round Changes

- Added `ClaimAssessment` plus shared `assess_claim()` in `tools/aris_geo/grading.py`.
- Stopped treating every numeric `D` claim as a noise-floor downgrade; the flag now requires the actual configured engine-floor condition.
- Added deterministic claim-level orange labels for:
  - `A/B 候选声称仅由供应商域名来源支撑`
  - `A/B 候选声称的第三方报告来源均标记为疑似投放内容`
- Added deterministic orange label `投毒指纹命中 ≥3 项` when three or more distinct non-empty poisoning fingerprints are present.
