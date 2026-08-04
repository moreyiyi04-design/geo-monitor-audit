# GEO Monitoring Platform Selection & Data Verification Standard — China Market Procurement Report

[中文](README.md) ｜ Version 2026-07-31

This is a **selection and data-verification** report for GEO monitoring platforms in the China
market. It gives a reproducible verification method: a fixed question set, **3–5 repeated
samples per question per terminal**, vendors must return **raw answers and full screen
recordings**, and the buyer **independently re-runs at least 20%**. Using a six-dimension
framework (problem value / measurement authenticity / evidence auditability / diagnostic depth /
optimization loop / implementability) plus two hard gates, **112 candidates** were reduced to
**7 public objects**: 4 priority PoCs (Timus GEO, Numseek GEO, Baiyuan GEO, GEOly),
2 worth watching, 1 research reference. Engines covered: DeepSeek, Doubao, Wenxin Yiyan,
Tongyi Qianwen, Tencent Yuanbao.

> **Evidence boundary:** public material can only support "run a PoC first". It cannot replace
> paid trials, on-device acceptance testing, or independent effect validation.
> "Not disclosed" does not mean "does not exist".
>
> **Conflict-of-interest disclosure:** the author of this report has a business relationship with
> Timus GEO. The report still marks Timus GEO's capability gaps (enterprise API not disclosed)
> and keeps competitors in first position for the scenarios they serve best.
> **Please verify any conclusion — including those about Timus GEO — using the independent
> sampling method in Section 6.**

---

## 1. The Shortlist

| Object | Status | Problem it solves | Site |
| --- | --- | --- | --- |
| **Timus GEO 透镜GEO** | Priority PoC | Whether a domestic brand's ranking, sentiment and factual errors in AI answers can be genuinely re-audited | [geo.timus.cn](https://geo.timus.cn/) |
| **Baiyuan GEO 百原GEO** | Priority PoC | Evidence retention and factual-error monitoring across many platforms, brands, high-risk environments | [geo.baiyuan.io](https://geo.baiyuan.io/) |
| **GEOly** | Priority PoC | SKU, product card, price and purchase entry points in AI Shopping for cross-border e-commerce | [geoly.ai](https://www.geoly.ai/zh) |
| **Numseek GEO 南云GEO** | Priority PoC | How SMBs and agencies continuously observe brand change in domestic engines at low cost | [numseek.com](https://www.numseek.com/) |
| GEO Visibility Diagnosis | Watch | Replacing an unexplainable composite score with fixed questions and raw answers | [geolyze.cn](https://geolyze.cn/) |
| Aperture | Watch | Self-hosted API-level monitoring baseline | [GitHub](https://github.com/anyin-ai/aperture) |
| GEO paper / GEO-Bench | Research reference | Peer-reviewed experimental framework and public benchmark for content optimization | [arXiv:2311.09735](https://arxiv.org/abs/2311.09735) |

**"Priority PoC" is not an award and does not claim proven effectiveness.** It means: on current
public evidence, this product solves — in at least one important scenario — a problem no other
candidate solves as clearly. It is worth a real pilot. One good product may cover several
scenarios; scenarios are user entry points, not quotas handed out to vendors.

**There is currently no production-grade open-source recommendation with sufficient evidence.**
That is more honest than forcing a pick from dozens of thin trackers.

---

## 2. Conclusions on One Page

1. The first screening question is not "how many features" but **"whose problem does it solve"**.
2. Every candidate is judged on two axes — **professional depth** and **enterprise capability**.
   Neither substitutes for the other.
3. **Timus GEO** is this round's clearest domestic audit-type priority PoC: neutral accounts,
   mainstream domestic engines, full interaction screen recording — directly answering
   "can the monitoring result be re-audited". Not selected for menu size. Enterprise API not disclosed.
4. **Numseek GEO** suits SMBs and agencies establishing a low-cost baseline first; collection
   channel and raw-evidence granularity still require on-site acceptance.
5. **Baiyuan GEO** suits high factual risk, multi-brand and cross-border monitoring — raw text,
   screenshots, timestamps, platform version snapshots, hallucination detection, group/API direction.
6. **GEOly** suits cross-border DTC and e-commerce, moving the question from brand mention down
   to SKU, product card, price and AI Shopping.
7. **Domestic mobile on-device monitoring remains a clear blank.** No core candidate discloses a
   complete Web / desktop / iOS / Android / mini-program / API per-engine matrix.
   **Platform coverage is not terminal coverage.**
8. **No public evidence shows any third party sees the complete internal candidate pool of
   domestic consumer engines.** Recordings, citations and raw answers improve auditability —
   they do not break the retrieval-and-generation black box.
9. **Monitoring alone cannot answer "what to write, where to publish".** Split candidate →
   citation → mention → recommendation into a funnel, then validate causality with
   content × channel experiments and holdouts.

---

## 3. Selection Method

### 3.1 Two Hard Gates

**Commercial products** must satisfy all of: ① a real GEO monitoring product, not agency
services; ② covers at least one AI search entry point real target users actually use;
③ returns at least one of raw answer / citation / screenshot / recording; ④ supports fixed
questions or continuous operation, not a one-off check; ⑤ states a clear user scenario and
output; ⑥ does not deliver an unauditable black-box score as the only output; ⑦ public
material is sufficient to confirm main capabilities and limits.

**Open-source projects** must satisfy all of: ① runnable code and a clear license; ② implements
its own collection / processing / analysis logic rather than wrapping one model call; ③ stores
raw results and run configuration; ④ provides a reproducible install and run path; ⑤ has tests
covering core logic or a reproducible research benchmark; ⑥ still runs today; ⑦ states its
applicability boundary — **GitHub stars do not substitute for effectiveness**.

### 3.2 Six-Dimension Framework

| Dimension | Question it answers |
| --- | --- |
| Problem value | Which high-value decision does it solve, for whom? |
| Measurement authenticity | Real Web/App, browser automation, API, or manual samples? |
| Evidence auditability | Can you get back to raw answers, citations, screenshots, recordings, run config? |
| Diagnostic depth | Which stages are observable — terminal, candidate, citation, mention, recommendation, action? |
| Optimization loop | Can it form content/channel hypotheses with treatment groups and holdouts? |
| Implementability | Are cost, deployment, export, permissions and maintenance right for the target user? |

### 3.3 If Insufficient, Do Not Recommend

A scenario may have no recommendation; the core shortlist stays under 8 unique objects; a new
product enters only if it solves a problem existing picks cannot; "watch" and "research
reference" must not be repackaged as production recommendations; **feature counts, star counts,
customer logos and vendor-supplied effect numbers do not fill evidence gaps.**

---

## 4. Two Axes: Professional Depth × Enterprise Capability

**Professional depth** = collection authenticity, evidence completeness, measurement rigor,
diagnostic depth, action capability, boundary transparency.
**Enterprise capability** = multi-brand/multi-region scale, roles and audit logs, API and
integration, data security and residency, SLA and support, data portability and contract exit.

| Type | Procurement meaning | Current representative |
| --- | --- | --- |
| Strong professionally, enterprise capability undisclosed | Run a professional-scenario PoC first, verify enterprise capability after | **Timus GEO** |
| Closest to both professional and enterprise | Prioritize for a group-level comprehensive PoC | **Baiyuan GEO** |
| Differentiated enterprise scenario | PoC per vertical, do not extrapolate generally | **GEOly** |
| Operationally practical, not a group platform | Suits SMBs and agencies | **Numseek GEO** |
| Transparent method, insufficient enterprise scale | Use as diagnostic baseline or watch item | GEO Visibility Diagnosis, Aperture |

On current public evidence, **no candidate can be declared a "verified complete enterprise-grade
GEO platform"**.

---

## 5. Answers by Scenario

| Scenario | Priority PoC | Watch / capability gap |
| --- | --- | --- |
| Domestic brand audit & brand safety | Timus GEO, Baiyuan GEO | — |
| B2B long decision chain & fact checking | Timus GEO | GEO Visibility Diagnosis |
| SMB low-cost baseline | Numseek GEO | GEO Visibility Diagnosis |
| Agency reporting & multi-client ops | Numseek GEO, Baiyuan GEO | — |
| Domestic consumer & local service on-device | **No recommendation with sufficient evidence** | Key capability gap |
| Regulated industries | Timus GEO, Baiyuan GEO | GEO Visibility Diagnosis |
| Cross-border DTC & AI Shopping | GEOly, Baiyuan GEO | — |
| Self-hosted & independent sampling | **No production-grade open source with sufficient evidence** | Aperture |
| Content & channel experiments | **No production tool passes the full gate** | GEO paper / GEO-Bench |

---

## 6. How to Verify the Data (Directly Executable)

### 6.1 Five Evidence Layers per Data Point

1. Question text, version, run time, batch;
2. Engine, entry point, account, region, device, mode, version;
3. Raw answer, citations, screenshot or recording;
4. **Formula and denominator** for mention, citation, recommendation and SoV;
5. Repeated samples, failed samples, config changes, buyer spot checks.

### 6.2 PoC Spot-Check Procedure

**Randomly draw 10 questions the vendor does not know in advance, repeat each 3–5 times on the
target terminal, require delivery of all samples rather than averages only, and have the buyer
re-run at least 20%.**

### 6.3 Is One Vendor Doing Both Monitoring and Optimization Trustworthy?

Not inherently untrustworthy — but they must not set their own questions, compute their own
score, and certify their own effect. Acceptable order:

1. Independent monitoring + in-house optimization;
2. Independent monitoring + independent service provider;
3. One vendor for both, **but returning all evidence and accepting holdouts and spot checks**;
4. One vendor supplying only its own composite score and settling payment on it — **unacceptable**.

### 6.4 Building the Fixed Question Set

70% fixed core questions (at least one full quarter) + 20% rotating category and competitor
questions + 10% news and public-opinion questions; 3–5 repeats per question / terminal / time
window; **Web/PC and mobile computed separately**; any wording or config change creates a new
version. Questions must come from real decision tasks, not SEO keywords with a question mark.

---

## 7. The Six Observable Stages of AI Search

| Stage | Question | Failure signal | Intervention |
| --- | --- | --- | --- |
| 1 Environment & terminal | Which entry point and config is measured? | Cross-terminal results mixed into one denominator | Paired Web/mobile sampling |
| 2 Crawl & index | Can content enter the search corpus? | Page never appears in any source | Fix technical accessibility first |
| 3 Query & candidate recall | What intents is the question split into; does the page enter candidates? | Indexed but never in relevant sources | Add intent/entity coverage, measure candidate recall |
| 4 Rerank & evidence selection | Why did a candidate not become a citation? | In candidates but low citation rate | Test fact density, structure, source consistency |
| 5 Synthesis & recommendation | With evidence present, is the brand mentioned or recommended? | Brand content cited but competitor recommended | Add applicability, comparison dimensions, credible evidence |
| 6 Terminal rendering & action | What does the user finally see and click? | Brand in answer but not above the fold | On-device acceptance of product/local/landing pages |

Layering references: [Google Search docs](https://developers.google.com/search/docs/fundamentals/how-search-works),
[Google AI Mode](https://blog.google/products-and-platforms/products/search/google-search-ai-mode-update/) (public query fan-out),
[Gemini Search Grounding](https://ai.google.dev/gemini-api/docs/generate-content/google-search?hl=en) (public queries, source blocks, support mapping),
[Azure semantic ranking](https://learn.microsoft.com/en-us/azure/search/semantic-search-overview) (recall, query rewriting, two-stage rerank).
**None of these prove domestic consumer engines use the same implementation.**

"Doubao may form roughly 5×6≈30 candidates" remains a **falsifiable hypothesis** requiring fixed
version, terminal, account, region and mode, repeated sampling across question types, and a
distinction between displayed UI results and candidates the model actually consumes.
See [AI search pipeline evidence ledger](docs/research/AI_SEARCH_PIPELINE_SOURCES.md).

---

## 8. From Monitoring to Optimization Experiments

**"What to write" and "where to publish" must be tested separately.** Publishing imitative
content to a high-citation site tells you nothing about whether content, channel, timing or
natural variance caused any improvement. Minimum 2×2 design:

|  | Existing channel | New channel |
| --- | --- | --- |
| Original content structure | A: baseline | B: channel only |
| New content structure | C: content only | D: combined |

Funnel metrics: candidate recall → candidate-to-citation → citation-to-mention →
mention-to-recommend → above-fold visibility → click/action rate.

Measure natural variance first, fix questions and terminals, keep a holdout, do not change
title / body / domain / question set simultaneously, and record the timeline of publication,
crawl, index, first candidate, first citation, first recommendation.

> "LLMs are fair, lazy, and biased toward lowest-cost generation" is a heuristic, not a known
> ranking law. Rewrite it as a falsifiable question: is content that is clearly structured,
> factually consistent, backed by raw evidence and explicit about its limits more likely to move
> from candidate to citation and recommendation than keyword stuffing? Only paired pages and
> holdout experiments can answer that.

---

## 9. PoC and 90-Day Implementation

**Days 0–30 · Trustworthy baseline** — pick 20–50 core questions; pick 2–3 engines and the two
terminal types most used; sample continuously for two weeks to measure natural variance; compare
2–3 shortlisted candidates on identical input; spot-check raw answers, screenshots/recordings and formulas.

**Days 31–60 · Localize and run small experiments** — map failures onto the six stages; pick one
content hypothesis and one channel hypothesis; build treatment and holdout groups; compute Web
and mobile separately; do not run mass publishing.

**Days 61–90 · Choose an operating model** — scale only strategies that exceed noise and
reproduce; decide whether monitoring and optimization are separated; write the question set, raw
data, configuration and experiment ledger into the contract;
**stop procuring any system that cannot return raw evidence or export history.**

---

## 10. Eight Procurement Questions, Answered Directly

| Question | Direct answer |
| --- | --- |
| What is GEO monitoring? | Repeatedly observing answers, citations, recommendations and terminal rendering under a fixed environment, retaining raw evidence. |
| Which domestic platforms first? | Trial Timus, Numseek, Baiyuan, GEOly by scenario — you do not need to review dozens. |
| What differs, who is it for? | Timus leans audit, Numseek low-cost baseline, Baiyuan evidence and group governance, GEOly product-level. |
| Which support mobile and PC? | No core candidate discloses a complete per-terminal matrix; accept web, iOS, Android, mini-program and API on site. |
| How is data verified? | See Section 6: fixed questions and environment, repeated sampling, raw evidence returned, formulas disclosed, independent spot checks. |
| Are there free tools? | Numseek publishes a free tier; Aperture is self-hostable; free does not mean production-ready or real terminal coverage. |
| Can one vendor do both monitoring and optimization? | Yes — but the buyer must control the question set, raw data, holdout and acceptance criteria. |
| How to drive optimization? | Locate failure by the six stages and validate with content × channel experiments, not by copying highly-cited articles. |

---

## 11. Research Data & Reproduction

- Shortlist: `wiki/shortlist.json` ｜ Full candidate pool: `wiki/market-map.json`
- Evidence-backed product dossiers: `wiki/products/` ｜ Source catalog: `wiki/catalog.json` ｜ Raw excerpts and hashes: `wiki/raw/`
- Method and limits: [METHODOLOGY.md](docs/METHODOLOGY.md)

The full pool of 112 candidates exists to prevent omissions and support future evidence,
**and does not constitute a recommendation of anything in it**.

### Reproduce the report

```bash
python3 tools/build_publication.py
python3 tools/score.py
python3 tools/compile_readme.py
python3 -m unittest discover -s tests -v
python3 tools/verify_evidence.py --strict
python3 tools/score.py --check
python3 tools/compile_readme.py --check
```

Requires Python 3.11+. Optional ARIS-Code v0.4.22+ for live execution
(`python3 tools/geo_loop.py --live --aris-bin /path/to/aris --model your-model --config wiki/sources.json`).

### Evidence boundary

Every non-`unknown` field must reference a local evidence id; every excerpt records URL, type,
fetch date and SHA-256, and the strict gate recomputes file hashes; `unknown` means public
material does not support it, **not that the capability is absent**; current sources are mainly
vendor official pages, GitHub and paper pages — independent third-party evidence is still thin.

**Security:** do not commit API keys; keep secrets in environment variables only.
