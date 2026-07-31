# Methodology

## Publication scope

ARIS-GEO evaluates public evidence about GEO/AIO/AEO software, open-source tools,
agent skills, and reference research. It does not perform GEO on a brand and does
not test whether a vendor can change live answer-engine rankings.

The 2026-07-31 publication separates breadth from depth. `wiki/market-map.json`
is a 112-object dated discovery snapshot spanning dedicated GEO vendors, incumbent
SEO-suite modules, domestic China products, self-hosted projects, agent-skill
packs, and academic testbeds. Nineteen representative products, including eight
domestic or Greater China products, also have evidence-gated deep profiles. The
domestic-first decision analysis is published in `docs/CHINA_MARKET.md`; overseas
products remain in the map as capability references. The synthetic Profound fixture under
`tests/fixtures/` exists only for regression tests and is excluded from publication.

## Selection

Candidates came from official product pages, public GitHub discovery, and academic
indexes. A human inclusion gate retained products with an identifiable official
source and enough material to classify their delivery form. This creates a
self-referential selection bias: products already good at GEO are easier to discover.
China-only products without accessible public documentation are underrepresented.

`wiki/market-map.json` records identity-level discovery; `wiki/catalog.json`
records the accepted deep-profile source set. Products are never promoted into
deep scoring automatically from a search result.

Market-map inclusion requires an identifiable public product or repository page
and a direct GEO, AEO, LLM-visibility, AI-search optimization, or AI-citation use
case. Consultancies without a distinct product, generic crawling infrastructure,
dead domains, and conventional SEO tools without a specific AI-search module are
excluded. A `market-map-only` entry has not passed the field-level evidence gate
and must not be interpreted as an endorsement or full evaluation.

## Evidence capture

Each evidence record contains:

- a stable local id;
- the public URL and source kind;
- the observation date;
- a short attributed extract, not a full copied page;
- the SHA-256 of that local extract;
- a paid-placement suspicion bit.

The publication builder writes extracts and profiles from the reviewed catalog.
`verify_evidence.py --strict` checks every non-unknown research envelope, source id,
path, hash, confidence value, and the two-way `unknowns[]` inventory.

The current report relies mainly on first-party pages and primary GitHub/paper
records. That is sufficient for product shape, disclosed pricing, and stated
methodology, but not for validating vendor outcome claims. Independent case-study
and registry coverage is an explicit gap.

## Platform and channel separation

An engine name is not a collection channel. “Supports DeepSeek” does not establish
whether observations came from browser/web, a desktop client, iOS, Android,
mini-program, or API. The domestic analysis therefore reports channel coverage
only when the public source says so and keeps undisclosed surfaces unknown.

Mobile/PC comparisons require paired samples with the same prompt and time window.
The comparison must record login state, region and location permission, search or
reasoning mode, model/version, session-reset method, repeat count, and evidence
retention. Results from consumer App surfaces and APIs must not share one SoV
denominator unless the report explicitly labels and weights the channels.

## Confidence and effect grades

Research fields use one of:

- `stated`: directly supported by the cited public extract;
- `inferred`: a bounded inference with a written note;
- `unknown`: public evidence in this run did not support an answer.

「未披露」不等于「没有」.

Effect claims receive A–E grades:

- A: authoritative/academic evidence or public methodology plus obtainable data;
- B: qualifying independent third-party validation;
- C: first-party claim with denominator or timeframe;
- D: first-party number without enough measurement context;
- E: no quantitative support.

Python recomputes grades and downgrades claims when the source is vendor-hosted,
suspected paid placement, or below a known measurement-noise floor. The report has
only three quantified outcome claims: the GEO paper’s experimental result and two
first-party commercial claims. It does not generalize any of them to the whole market.

## Scores

All scores are deterministic and reproducible:

- `transparency`: public pricing, public methodology, verifiable entity, disclosed
  data source, disclosed refund terms;
- `verifiability`: weighted mean of recomputed A–E effect grades;
- `lock_in_risk`: data export, vendor-hosted content, contract length, annual-only
  billing, and history portability;
- `measurement_rigor`: browser capture, disclosed repeated sampling, confidence
  intervals, noise floor, and public share-of-voice formula;
- `oss_health`: category-specific license, activity, contributor, release, test, and
  academic-reproducibility checks.

For closed products, `oss_health` is `0` as “not applicable in the numeric schema”,
not as a quality judgment. No composite total or ordinal ranking is published.

## GitHub snapshot

GitHub repository counts were read from the public API on 2026-07-31. Repositories
created within the preceding year use their visible contributor count as the
12-month count. A recent `pushed_at` timestamp establishes at least one recent
commit but is not expanded into an exact 90-day count. Test coverage is marked true
only when the reviewed evidence supports tests of project-owned logic; otherwise it
remains false rather than guessed.

## Live orchestration and privacy

The live driver supports direct-URL fetches, optional Tavily discovery, GitHub health
collection, ARIS model phases, isolated vendor/skeptic/arbiter inboxes, deterministic
patch application, and all publication gates.

Model phases necessarily transmit their staged inputs to the configured model
provider. The committed 2026-07-31 report was curated in the current Codex session and
does not depend on transmitting the private repository or its skill files to DeepSeek.
The ARIS 0.4.22 binary was checksum-verified in a temporary directory and is not
committed.

## Known v1 limitations

1. 国内产品的逐模型 Web/App/小程序采集矩阵普遍未公开，本报告不能替厂商补全。
2. 国内选型已按品牌类型分层，但尚未获得采购账号进行手机与 PC 配对实测。
3. 公开页面可能随时变更；本报告只对 `fetched_at` 当日快照负责。
4. 发现机制存在自指偏差，人工过闸只能缓解、不能消除。
5. 同一供应商的定价单位可能按 prompt、问题、关键词、引擎或 credit 变化。
6. 第一方页面大量缺少样本数、误差范围和噪声下限，因而不能支持效果比较。
7. 未登录产品、销售合同、真实导出质量、企业安全控制和售后体验均未实测。
8. 无综合总分排名。

## Label sunset

标签必须能消失. When later evidence discloses a method, price, export option, or
measurement control, refreshing the catalog and rerunning the deterministic builder
changes the affected envelopes and labels. Labels are dated observations, not
permanent judgments.
