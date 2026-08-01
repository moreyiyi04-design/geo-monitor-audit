<!-- ARIS-GEO:HANDWRITTEN:START -->
# ARIS-GEO

一份以中国市场为主、海外产品为参照的 GEO 监测采购与实施研究。

本版截至 **2026-07-31**，由两层结果组成：

- **最终决策报告**：先回答什么是 GEO 监测、国内有哪些平台、适合谁、移动/PC
  是否覆盖、数据如何验证、免费入口、利益冲突和监测驱动优化；
- **112 个对象的市场地图**：85 个海外、27 个国内，作为采购搜索面和海外能力参照；
- **19 个深度档案**：其中 8 个国内对象，对公开材料做字段级来源和未知项审查。

市场地图回答“有哪些”；深度档案回答“公开证据到底支持什么”。没有进入深度档案
不等于产品较差，只表示本轮尚未完成字段级核验。这不是总榜，不把不同形态压成一个
“第一名”。测试所用的合成 Profound 样本仍保留在 `tests/fixtures/`，但不参与报告。

## 最终决策报告

主要交付物是
**[GEO 监测平台决策报告：中国市场、数据可信度与优化闭环](docs/FINAL_REPORT.md)**。
它给出结论、六阶段 AI 搜索可观测链路、国内厂商比较、移动/PC 能力边界、免费入口、
数据复核、利益冲突控制、固定问题集和“内容 × 渠道”实验方法。下方全球地图只作附录。

## 结论先行

1. **监测是测量系统，不是优化本身。** 最终答案统计不能直接回答“写什么、发哪里”；
   需要把候选、引用、提及、推荐拆成漏斗，再做内容与渠道对照实验。
2. **国内已有可采购产品，没有通用第一名。** 透镜、独角兽、GTark、GEO工具、
   南云、GEO可见度诊断、百原和 GEOly 进入本轮证据化比较。
3. **没有公开证据证明任何一家看见国内消费端引擎的完整内部候选池。** 录屏、
   原始回答和引用提升可复核性，但不等于破解检索与生成黑盒。
4. **移动端与 PC 端必须分层。** 核心 8 家均未公开完整的 Web、桌面、iOS、
   Android、小程序、API 逐引擎矩阵；平台 Logo 不能作为终端覆盖证明。
5. **同一家做监测和优化可以合作，但不能自证。** 问题集、原始数据和 holdout
   必须由采购方控制，重大效果应独立抽检。
6. **先做 4–6 周 PoC。** 用同一问题集比较证据返还、跨端结果、重复采样波动和一次
   “内容 × 渠道”实验，再签长期合同。

## Requirements

- Python 3.11+
- Optional ARIS-Code v0.4.21+ for live execution (`v0.4.22+` recommended)

## Reproduce the report

```bash
python3 tools/build_publication.py
python3 tools/score.py
python3 tools/compile_readme.py
python3 -m unittest discover -s tests -v
python3 tools/verify_evidence.py --strict
python3 tools/score.py --check
python3 tools/compile_readme.py --check
```

`wiki/catalog.json` 是人工过闸的公开来源目录；`build_publication.py` 生成短摘录、哈希和
profile，之后所有等级、分数、风险标签和 README 表格都由 Python 机械生成。

## Evidence boundary

- 每个非 unknown 字段必须引用本地 evidence id。
- 每份短摘录记录 URL、类型、抓取日期和 SHA-256；严格门会重算文件哈希。
- `unknown` 表示“公开材料未支持”，不是“该能力不存在”。
- 本版以供应商官方页面、GitHub/论文原始页面为主；独立第三方证据覆盖仍不足。
- GitHub 健康数据来自 2026-07-31 的公共 API 快照；匿名 API 限额不适合大规模刷新。

## Optional live orchestration

```bash
python3 tools/geo_loop.py \
  --live \
  --aris-bin /path/to/aris \
  --model your-model \
  --config wiki/sources.json
```

Live handlers cover query planning, fetch, digest, profile, isolated
vendor/skeptic review, arbitration, deterministic patch application, verification and
README compilation. Direct public URLs work without Tavily; optional Tavily and
authenticated GitHub collection use environment variables only.

Model phases send the staged evidence and contracts to the configured external provider.
Run them only when that data-transfer boundary is acceptable. The committed report does
not depend on such an external model run.

## Security

Do not commit API keys. Keep secrets in environment variables only. Credentials are
never copied into persona inboxes, evidence files, cache keys or audit artifacts.

See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for selection bias, evidence grading,
score definitions and known limitations.
<!-- ARIS-GEO:HANDWRITTEN:END -->

<!-- ARIS-GEO:COMPILED:START -->
> 数据截至 2026-07-31
> 「未披露」≠「没有」；产品级证据、分数和风险字段保留在 wiki/products/。

### 附录：全球市场地图
| 产品 | 市场 | 类别 | 形态 | 开放性 | 覆盖级别 | 官网 |
| --- | --- | --- | --- | --- | --- | --- |
| Adobe LLM Optimizer | overseas | 企业级一体化平台, 内容优化 | SaaS | closed | market-map-only | https://business.adobe.com/products/llm-optimizer.html |
| AEO Mentions Crawler | overseas | 监测/可见性追踪 | 自托管应用 | open-source | market-map-only | https://github.com/federicodeponte/aeo-mentions-crawler |
| AEO Platform | overseas | 监测/可见性追踪 | CLI | open-source | market-map-only | https://github.com/webappski/aeo-platform |
| Agent Skills Marketing GEO | overseas | Agent Skill / Prompt Pack | Agent Skill Library | open-source | market-map-only | https://github.com/whyashthakker/agent-skills-marketing |
| Ahrefs Brand Radar | overseas | 企业搜索套件, 监测/可见性追踪 | SaaS | closed | market-map-only | https://ahrefs.com/brand-radar |
| AI Growth | domestic | 监测/可见性追踪, 内容优化 | SaaS | closed | market-map-only | https://zia.com.cn/ |
| AI Monitor | overseas | 监测/可见性追踪 | SaaS / 开源核心 | hybrid | market-map-only | https://getaimonitor.com/ |
| AI Rank Tracker by DEJAN | overseas | 监测/可见性追踪 | Web Tool | closed | market-map-only | https://airank.dejan.ai/ |
| AiCarma | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://aicarma.com/ |
| AirOps | overseas | 内容优化, 工作流自动化 | SaaS | closed | market-map-only | https://www.airops.com/ |
| Am I on AI? | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://amionai.com/ |
| Aperture | overseas | 监测/可见性追踪 | 自托管应用 | open-source | deep-profile | https://github.com/anyin-ai/aperture |
| AppearOnAI | overseas | 技术审计, 内容优化 | SaaS | closed | market-map-only | https://appearonai.com/ |
| AthenaHQ | overseas | 一体化平台, 监测/可见性追踪 | SaaS | closed | market-map-only | https://athenahq.ai/ |
| Attensira | overseas | 一体化平台, 监测/可见性追踪 | SaaS | closed | market-map-only | https://attensira.com/ |
| 百原GEO | domestic | 一体化平台, 监测/可见性追踪, 幻觉检测 | SaaS | closed | deep-profile | https://geo.baiyuan.io/ |
| Bluefish AI | overseas | 企业级一体化平台, 品牌安全 | SaaS | closed | market-map-only | https://www.bluefishai.com/ |
| Botify | overseas | 企业搜索套件, 技术审计 | SaaS | closed | market-map-only | https://www.botify.com/ |
| BrandBeacon | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.brandbeacon.ai/ |
| BrandInAI | overseas | 监测/可见性追踪, 品牌叙事 | SaaS | closed | market-map-only | https://brandinai.com/ |
| Brandlight | overseas | 企业级一体化平台, 品牌叙事 | SaaS | closed | market-map-only | https://www.brandlight.ai/ |
| BrightEdge AI Hyper Cube | overseas | 企业搜索套件, 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.brightedge.com/ |
| ChatFeatured | overseas | 监测/可见性追踪, 内容优化 | SaaS | closed | market-map-only | https://chatfeatured.com/ |
| Cognizo | overseas | 监测/可见性追踪, 客户旅程 | SaaS | closed | market-map-only | https://cognizo.ai/ |
| Conductor | overseas | 企业搜索套件, 一体化平台 | SaaS | closed | market-map-only | https://www.conductor.com/ |
| DeepSeekGEO | domestic | 品牌诊断, 监测/可见性追踪 | SaaS | closed | market-map-only | https://deepseekgeo.com/ |
| 豆智语义科技 DZOS | domestic | 一体化平台, 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.dzgoogle.com/ |
| E-GEO Testbed | overseas | 学术基准 | 论文与测试床 | hybrid | deep-profile | https://arxiv.org/abs/2511.20867 |
| Evertune | overseas | 企业级一体化平台, 品牌叙事 | SaaS | closed | market-map-only | https://www.evertune.ai/ |
| Exanimo.ai | overseas | 代理商白标, 监测/可见性追踪 | SaaS | closed | market-map-only | https://exanimo.ai/ |
| FalconRank.ai | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://falconrank.ai/ |
| Gauge | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.withgauge.com/ |
| 极客GEO | domestic | 一体化平台, GEO 服务 | 平台 / 服务 | closed | market-map-only | https://geo.dso100.com/ |
| GeeoAI | domestic | 品牌诊断, 竞品分析, 内容优化 | SaaS | closed | market-map-only | https://geeoai.com/ |
| GenRank | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://genrank.io/ |
| 17CE GEO检测 | domestic | 品牌诊断, GEO 检测 | Web Tool | closed | market-map-only | https://geo.17ce.com/?lang=zh_cn |
| GEO/AEO Tracker | overseas | 监测/可见性追踪 | 自托管应用 | open-source | deep-profile | https://github.com/danishashko/geo-aeo-tracker |
| GEO: Generative Engine Optimization | overseas | 学术基准 | 论文与基准 | hybrid | deep-profile | https://arxiv.org/abs/2311.09735 |
| GEO Optimizer Skill | overseas | 技术审计, Agent Skill / Prompt Pack | CLI / Agent Skill | open-source | deep-profile | https://github.com/Auriti-Labs/geo-optimizer-skill |
| 中国GEO服务平台 | domestic | GEO 服务, 内容优化 | 平台 / 服务 | closed | market-map-only | https://geo.org.cn/ |
| 见川GEO | domestic | 监测/可见性追踪, 品牌诊断 | SaaS | closed | market-map-only | https://www.georadar.top/ |
| GEO-Star | domestic | GEO 服务, 内容优化 | 平台 / 服务 | closed | market-map-only | https://www.geo-star.com/ |
| GEO AI搜索优化 | domestic | 一体化平台, 监测/可见性追踪 | SaaS | closed | deep-profile | https://www.geo-tool.cn/ |
| GEOEYE | domestic | 一体化平台, 监测/可见性追踪, 内容优化 | SaaS | closed | market-map-only | https://geobullseye.com/ |
| GEOly | domestic | 电商/DTC, 监测/可见性追踪, AI Shopping | SaaS / API / MCP | closed | deep-profile | https://www.geoly.ai/zh |
| GEO可见度诊断 | domestic | 品牌诊断, 监测/可见性追踪 | Web Tool / 服务商工具 | closed | deep-profile | https://geolyze.cn/ |
| Geometrika | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://geometrika.dev/ |
| GEOROI | domestic | 一体化平台, 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.georoi.cn/ |
| GEO Skills | overseas | Agent Skill / Prompt Pack | Agent Skill | open-source | deep-profile | https://github.com/Cognitic-Labs/geoskills |
| 工蜂云 | domestic | 品牌诊断, 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.gongfengyun.com/ |
| Goodie AI | overseas | 一体化平台, 内容优化 | SaaS | closed | market-map-only | https://higoodie.com/ |
| Goose Skills AEO Visibility | overseas | Agent Skill / Prompt Pack | Agent Skill Library | open-source | market-map-only | https://github.com/gooseworks-ai/goose-skills |
| GrackerAI | overseas | 内容优化, 监测/可见性追踪 | SaaS | closed | market-map-only | https://gracker.ai/ |
| GTark | domestic | 一体化平台, 监测/可见性追踪 | SaaS | closed | deep-profile | https://www.gtark.com/ |
| Heeb.ai | overseas | 监测 API, 可见性追踪 | API / SaaS | closed | market-map-only | https://heeb.ai/ |
| Hikoo | overseas | 一体化平台, 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.tryhikoo.com/ |
| 君荣AI GEO | domestic | GEO 服务, 内容优化 | 平台 / 服务 | closed | market-map-only | https://geo.junrongopc.com/ |
| Knowatoa | overseas | 监测/可见性追踪, 技术审计 | SaaS | closed | market-map-only | https://knowatoa.com/ |
| 鲲擎AI | domestic | 监测/可见性追踪, 内容优化 | SaaS | closed | market-map-only | https://risingtec.cn/ |
| LightSite AI | overseas | 内容优化, 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.lightsite.ai/ |
| LLMO Metrics | overseas | 监测/可见性追踪, 优化建议 | SaaS | closed | market-map-only | https://llmometrics.com/ |
| LLMrefs | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://llmrefs.com/ |
| Lorelight | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://lorelight.ai/ |
| Mangools AI Search Watcher | overseas | 企业搜索套件, 监测/可见性追踪 | SaaS | closed | market-map-only | https://mangools.com/ |
| Marketing Skills AI SEO | overseas | Agent Skill / Prompt Pack | Agent Skill Library | open-source | market-map-only | https://github.com/coreyhaines31/marketingskills |
| ModelMonitor | overseas | 监测 API, 品牌声誉 | API / SaaS | closed | market-map-only | https://modelmonitor.ai/ |
| Monroya | overseas | 一体化平台, 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.monroya.ai/ |
| Nightwatch | overseas | SEO 排名与 AI 追踪 | SaaS | closed | market-map-only | https://nightwatch.io/ |
| Nuggt | overseas | 代理商平台, 生成式搜索分析 | SaaS | closed | market-map-only | https://beta.nuggt.io/ |
| 南云GEO | domestic | 监测/可见性追踪, 竞品分析 | SaaS | closed | deep-profile | https://www.numseek.com/ |
| OneGlanse | overseas | 监测/可见性追踪 | 自托管应用 | open-source | market-map-only | https://github.com/aryamantodkar/oneglanse |
| OtterlyAI | overseas | 监测/可见性追踪 | SaaS | closed | deep-profile | https://otterly.ai/ |
| Peec AI | overseas | 监测/可见性追踪, 代理商报告 | SaaS | closed | market-map-only | https://peec.ai/ |
| Peekaboo | overseas | 监测/可见性追踪, 竞品分析 | SaaS | closed | market-map-only | https://aipeekaboo.com/ |
| Profound | overseas | 一体化平台, 监测/可见性追踪 | SaaS | closed | deep-profile | https://www.tryprofound.com/ |
| Promptmonitor | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.promptmonitor.io/ |
| Promptwatch | overseas | 监测 API, 可见性追踪 | API / SaaS | closed | market-map-only | https://promptwatch.com/ |
| Quno.ai | overseas | 监测/可见性追踪, 内容优化 | SaaS | closed | market-map-only | https://quno.ai/ |
| Qwairy | overseas | 一体化平台, 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.qwairy.co/ |
| Ranketta | overseas | 监测/可见性追踪, 电商内容优化 | SaaS | closed | market-map-only | https://ranketta.com/ |
| Rankscale | overseas | 监测/可见性追踪 | SaaS | closed | deep-profile | https://rankscale.ai/ |
| RankTera | overseas | SEO 与 GEO 套件, 监测/可见性追踪 | SaaS | closed | market-map-only | https://ranktera.com/ |
| Scalenut | overseas | 内容优化, 企业搜索套件 | SaaS | closed | market-map-only | https://www.scalenut.com/ |
| Scrunch AI | overseas | 一体化平台, 监测/可见性追踪 | SaaS | closed | deep-profile | https://scrunch.com/ |
| SE Ranking AI Visibility Tracker | overseas | 企业搜索套件, 监测/可见性追踪 | SaaS | closed | market-map-only | https://seranking.com/ |
| Search Visibility | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://search-visibility.ai/ |
| Searchify | overseas | 一体化平台, 中小企业 | SaaS | closed | market-map-only | https://searchify.ai/ |
| Seerly AIRO | overseas | AI 搜索优化, 内容优化 | SaaS | closed | market-map-only | https://seerly.app/ |
| Semrush AI Visibility Toolkit | overseas | 企业搜索套件, 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.semrush.com/kb/1496-getting-started-with-ai-visibility-toolkit |
| Senso.ai | overseas | 内容优化, CMS 工作流 | SaaS | closed | market-map-only | https://senso.ai/ |
| SEO & GEO Skills Library | overseas | Agent Skill / Prompt Pack | Agent Skill Library | open-source | deep-profile | https://github.com/aaron-he-zhu/seo-geo-claude-skills |
| seoClarity | overseas | 企业搜索套件, 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.seoclarity.net/ |
| 商脉通GEO | domestic | 一体化平台, GEO 服务 | 平台 / 服务 | closed | market-map-only | https://www.smt.wang/ |
| Share of Model by Jellyfish | overseas | 监测/可见性追踪, 品牌研究 | 平台 / 服务 | closed | market-map-only | https://www.jellyfish.com/ |
| Similarweb AI Search Intelligence | overseas | 企业搜索套件, 监测/可见性追踪 | SaaS | closed | market-map-only | https://aisearch.similarweb.com/ |
| 搜搜果 | domestic | 监测/可见性追踪 | SaaS | closed | market-map-only | https://www.sousougeo.com/ |
| Surfer AI Tracker | overseas | 内容优化, 监测/可见性追踪 | SaaS | closed | market-map-only | https://surferseo.com/ |
| Tesseract by AdLift | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://tesseract.adlift.com/ |
| 透镜GEO | domestic | 一体化平台, 监测/可见性追踪, 品牌口碑 | SaaS | closed | deep-profile | https://geo.timus.cn/ |
| Toprank GEO Optimizer Skill | overseas | Agent Skill / Prompt Pack | Agent Skill Library | open-source | market-map-only | https://github.com/nowork-studio/toprank |
| Trackerly.ai | overseas | 监测/可见性追踪, 代理商报告 | SaaS | closed | market-map-only | https://trackerly.ai/ |
| Trakkr.ai | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://trakkr.ai/ |
| 独角兽GEO | domestic | 一体化平台, 监测/可见性追踪 | SaaS | closed | deep-profile | https://geo.yueyuezi.com/ |
| Visalytica | overseas | 监测/可见性追踪, 内容优化 | SaaS | closed | market-map-only | https://www.visalytica.com/ |
| Waikay | overseas | 监测/可见性追踪, 事实与声誉 | SaaS | closed | market-map-only | https://waikay.io/ |
| Writesonic GEO Suite | overseas | 一体化平台, 内容优化 | SaaS | closed | market-map-only | https://writesonic.com/generative-engine-optimization-geo |
| XFunnel | overseas | 一体化平台, 客户旅程 | SaaS | closed | market-map-only | https://xfunnel.ai/ |
| 吸晶智能 | domestic | GEO 服务, 内容优化 | 平台 / 服务 | closed | market-map-only | https://www.xjgeo.com/ |
| Yext | overseas | 企业搜索套件, 知识管理 | SaaS | closed | market-map-only | https://www.yext.com/ |
| 嬴政GEO | domestic | 一体化平台, 监测/可见性追踪 | 平台 / 服务 | closed | market-map-only | https://www.geoc.cc/ |
| 中科信枢GEO | domestic | 品牌诊断, 监测/可见性追踪 | SaaS | closed | market-map-only | https://zkxinshu.com/ |
| ZipTie.dev | overseas | 监测/可见性追踪 | SaaS | closed | market-map-only | https://ziptie.dev/ |
<!-- ARIS-GEO:COMPILED:END -->
