<!-- ARIS-GEO:HANDWRITTEN:START -->
# ARIS-GEO

一份以国内选型为主、海外产品为参照，带来源、证据等级、未知项和可复算分数的
GEO / AEO 工具横向报告。

本版截至 **2026-07-31**，由两层结果组成：

- **112 个对象的市场地图**：覆盖 85 个海外对象、27 个国内对象，包括商业平台、
  传统 SEO 厂商 AI 模块、开源工具、Agent Skill 与学术基准；
- **19 个深度档案**：其中 8 个国内对象，对有足够公开材料的代表产品进行字段级
  证据、评分和风险审查。

市场地图回答“有哪些”；深度档案回答“公开证据到底支持什么”。没有进入深度档案
不等于产品较差，只表示本轮尚未完成字段级核验。这不是总榜，不把不同形态压成一个
“第一名”。测试所用的合成 Profound 样本仍保留在 `tests/fixtures/`，但不参与报告。

## 国内 GEO 厂商专项分析

国内市场、移动端/PC端差异、厂商能力分层和品牌类型适配，见
**[国内 GEO 厂商专项分析与选型指南](docs/CHINA_MARKET.md)**。该文档是本版主要
决策入口；下方全球市场地图用于补充广度和海外能力参照。

## 结论先行

1. **国内市场不是海外产品的缩小版。** 本轮识别 27 个国内/大中华区对象，覆盖
   可见度监测、诊断、内容/分发闭环、代运营服务和跨境电商数据平台；应先按产品形态
   分组，再比较能力。
2. **平台覆盖不等于终端覆盖。** “支持豆包/DeepSeek/元宝”不能证明同时采集 Web、
   PC 客户端、iOS/Android App、小程序和 API。公开终端矩阵缺失，是国内采购最突出
   的测量风险。
3. **移动端与 PC 端需要分层采样。** 登录历史、地区/定位、搜索和深度思考开关、
   App 专属商品卡/本地入口、引用呈现都可能改变可观察答案；不同终端不能混在同一
   SoV 分母中。
4. **透镜GEO已进入重点深档。** 官网公开支持 5 个国内主流模型、中立账号模拟、
   日级追踪和完整屏幕录制，适合重视审计与品牌安全的候选；但逐模型 Web/App 采集
   矩阵仍未公开，移动端能力需要采购试点验证。
5. **品牌类型决定选型。** 国内消费/本地品牌优先手机端和中文模型；B2B优先长问题、
   引用和原始证据；电商/DTC优先 SKU、商品卡、价格与 Feed；受监管行业优先录屏/
   快照、固定口径、权限和留存。
6. **公开定价不等于可横向比价。** 有的平台按 prompt，有的按问题/关键词，有的按
   credit 和引擎次数计费；报告保留原始单位，不用伪精确换算制造可比性。
7. **第一方效果数字不能当独立证据。** Scrunch 的 4x 与 GTark 的 32%→94.81%
   均按 D 级处理；GEO 论文的“最高 40%”有公开论文与实验基准，但仍只代表其设定。
8. **开源不自动等于成熟。** 本版把许可证、贡献者、近期提交、发布和业务测试分开
   记录；星标不进入总分，也不作为产品质量代理。

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
> 「未披露」≠「没有」；下表仅呈现已公开且有证据的字段。

### 市场地图
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

### 选型矩阵
| 产品 | slug | 市场 | 形态 | 开放性 | 核心类别 |
| --- | --- | --- | --- | --- | --- |
| Aperture / Aperture | aperture | overseas | Self-hosted web application | open-source | 监测/可见性追踪 |
| 百原GEO / BaiYuan GEO | baiyuan_geo | domestic | SaaS | closed | 一体化平台 |
| E-GEO 电商测试床 / E-GEO: A Testbed for Generative Engine Optimization in E-Commerce | e_geo_testbed | overseas | Research paper and testbed | source-available | 学术参考实现 |
| GEO/AEO Tracker / GEO/AEO Tracker | geo_aeo_tracker | overseas | Self-hosted web application | open-source | 监测/可见性追踪 |
| 生成式引擎优化（GEO） / GEO: Generative Engine Optimization | geo_generative_engine_optimization | overseas | Research paper and benchmark | source-available | 学术参考实现 |
| GEO Optimizer Skill / GEO Optimizer Skill | geo_optimizer_skill | overseas | Agent skill and audit toolkit | open-source | agent-skill/prompt-pack |
| GEO AI搜索优化 / GEO AI Search Optimization | geo_tool_cn | domestic | SaaS | closed | 一体化平台 |
| GEOly / GEOly | geoly_ai | domestic | SaaS / API / MCP | closed | 电商/DTC |
| GEO可见度诊断 / GEO Visibility Diagnosis | geolyze | domestic | Web Tool / service-provider workflow | closed | 品牌诊断 |
| GEO Skills / GEO Skills | geoskills | overseas | Agent skill suite | open-source | agent-skill/prompt-pack |
| GTark / GTark | gtark | domestic | SaaS | closed | 一体化平台 |
| 南云GEO / NumSeek | numseek | domestic | SaaS | closed | 监测/可见性追踪 |
| OtterlyAI / OtterlyAI | otterlyai | overseas | SaaS | closed | 监测/可见性追踪 |
| Profound / Profound | profound | overseas | SaaS | closed | 一体化平台 |
| Rankscale / Rankscale | rankscale | overseas | SaaS | closed | 监测/可见性追踪 |
| Scrunch AI / Scrunch AI | scrunch_ai | overseas | SaaS | closed | 一体化平台 |
| SEO & GEO Skills Library / SEO & GEO Skills Library | seo_geo_claude_skills | overseas | Agent skill library | open-source | agent-skill/prompt-pack |
| 透镜GEO / TIMUS GEO | timus_geo | domestic | SaaS | closed | 一体化平台 |
| 独角兽GEO / Unicorn GEO | unicorn_geo | domestic | SaaS | closed | 一体化平台 |

### 分数
| 产品 | transparency | verifiability | lock_in_risk | measurement_rigor | oss_health |
| --- | --- | --- | --- | --- | --- |
| Aperture / Aperture | 2 | 0 | 0 | 0 | 3 |
| 百原GEO / BaiYuan GEO | 2 | 0 | 0 | 1 | 0 |
| E-GEO 电商测试床 / E-GEO: A Testbed for Generative Engine Optimization in E-Commerce | 2 | 0 | 0 | 0 | 3 |
| GEO/AEO Tracker / GEO/AEO Tracker | 2 | 0 | 0 | 0 | 2 |
| 生成式引擎优化（GEO） / GEO: Generative Engine Optimization | 2 | 5 | 0 | 0 | 5 |
| GEO Optimizer Skill / GEO Optimizer Skill | 2 | 0 | 0 | 0 | 3 |
| GEO AI搜索优化 / GEO AI Search Optimization | 2 | 0 | 0 | 0 | 0 |
| GEOly / GEOly | 2 | 0 | 0 | 0 | 0 |
| GEO可见度诊断 / GEO Visibility Diagnosis | 2 | 0 | 0 | 0 | 0 |
| GEO Skills / GEO Skills | 2 | 0 | 0 | 0 | 3 |
| GTark / GTark | 4 | 1 | 0 | 1 | 0 |
| 南云GEO / NumSeek | 2 | 0 | 0 | 0 | 0 |
| OtterlyAI / OtterlyAI | 2 | 0 | 0 | 0 | 0 |
| Profound / Profound | 3 | 0 | 2 | 2 | 0 |
| Rankscale / Rankscale | 2 | 0 | 0 | 0 | 0 |
| Scrunch AI / Scrunch AI | 1 | 1 | 0 | 0 | 0 |
| SEO & GEO Skills Library / SEO & GEO Skills Library | 2 | 0 | 0 | 0 | 4 |
| 透镜GEO / TIMUS GEO | 2 | 0 | 0 | 0 | 0 |
| 独角兽GEO / Unicorn GEO | 3 | 0 | 0 | 1 | 0 |

### 产品档案表
| 产品 | 官网 | 类别 | 公开定价 |
| --- | --- | --- | --- |
| Aperture / Aperture | https://github.com/anyin-ai/aperture | 监测/可见性追踪 | 开源 / 自托管 |
| 百原GEO / BaiYuan GEO | https://geo.baiyuan.io/ | 一体化平台, 监测/可见性追踪, 幻觉检测 | — |
| E-GEO 电商测试床 / E-GEO: A Testbed for Generative Engine Optimization in E-Commerce | https://arxiv.org/abs/2511.20867 | 学术参考实现 | 不适用 |
| GEO/AEO Tracker / GEO/AEO Tracker | https://github.com/danishashko/geo-aeo-tracker | 监测/可见性追踪 | 开源 / 自托管 |
| 生成式引擎优化（GEO） / GEO: Generative Engine Optimization | https://arxiv.org/abs/2311.09735 | 学术参考实现 | 不适用 |
| GEO Optimizer Skill / GEO Optimizer Skill | https://github.com/Auriti-Labs/geo-optimizer-skill | agent-skill/prompt-pack | 开源 / 自托管 |
| GEO AI搜索优化 / GEO AI Search Optimization | https://www.geo-tool.cn/ | 一体化平台, 监测/可见性追踪 | 已公开 |
| GEOly / GEOly | https://www.geoly.ai/zh | 电商/DTC, 监测/可见性追踪, AI Shopping | — |
| GEO可见度诊断 / GEO Visibility Diagnosis | https://geolyze.cn/ | 品牌诊断, 监测/可见性追踪 | 未公开 |
| GEO Skills / GEO Skills | https://github.com/Cognitic-Labs/geoskills | agent-skill/prompt-pack | 开源 / 自托管 |
| GTark / GTark | https://www.gtark.com/ | 一体化平台, 监测/可见性追踪 | 已公开 |
| 南云GEO / NumSeek | https://www.numseek.com/ | 监测/可见性追踪, 竞品分析 | 已公开 |
| OtterlyAI / OtterlyAI | https://otterly.ai/ | 监测/可见性追踪 | 已公开 |
| Profound / Profound | https://www.tryprofound.com/ | 一体化平台, 监测/可见性追踪 | 已公开 |
| Rankscale / Rankscale | https://rankscale.ai/ | 监测/可见性追踪 | 已公开 |
| Scrunch AI / Scrunch AI | https://scrunch.com/ | 一体化平台, 监测/可见性追踪 | — |
| SEO & GEO Skills Library / SEO & GEO Skills Library | https://github.com/aaron-he-zhu/seo-geo-claude-skills | agent-skill/prompt-pack | 开源 / 自托管 |
| 透镜GEO / TIMUS GEO | https://geo.timus.cn/ | 一体化平台, 监测/可见性追踪, 品牌口碑 | — |
| 独角兽GEO / Unicorn GEO | https://geo.yueyuezi.com/ | 一体化平台, 监测/可见性追踪 | 已公开 |

### 标签清单
#### Aperture / Aperture
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 无覆盖自身逻辑的测试
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂

#### 百原GEO / BaiYuan GEO
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露

#### E-GEO 电商测试床 / E-GEO: A Testbed for Generative Engine Optimization in E-Commerce
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露

#### GEO/AEO Tracker / GEO/AEO Tracker
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 无覆盖自身逻辑的测试
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 贡献者集中于单人

#### 生成式引擎优化（GEO） / GEO: Generative Engine Optimization
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露

#### GEO Optimizer Skill / GEO Optimizer Skill
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 无覆盖自身逻辑的测试
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露

#### GEO AI搜索优化 / GEO AI Search Optimization
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露

#### GEOly / GEOly
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露

#### GEO可见度诊断 / GEO Visibility Diagnosis
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 无公开定价 / 仅年付 / 无试用 / 退款条款未公开
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露

#### GEO Skills / GEO Skills
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 无覆盖自身逻辑的测试
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 贡献者集中于单人
- 🟡 采集通道未披露

#### GTark / GTark
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟠 效果声称以 D/E 级为主

#### 南云GEO / NumSeek
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露

#### OtterlyAI / OtterlyAI
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露

#### Profound / Profound
- 🟡 不报告置信区间或误差范围
- 🟡 入门档仅覆盖单一引擎
- 🟡 入门档席位数未披露
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 无公开定价 / 仅年付 / 无试用 / 退款条款未公开
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟠 无数据导出 / 最低合约期 > 6 个月

#### Rankscale / Rankscale
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露
- 🟠 计价单位随监测范围膨胀

#### Scrunch AI / Scrunch AI
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露
- 🟠 效果声称以 D/E 级为主

#### SEO & GEO Skills Library / SEO & GEO Skills Library
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 无覆盖自身逻辑的测试
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
- 🟡 采集通道未披露

#### 透镜GEO / TIMUS GEO
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 入门档引擎数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂

#### 独角兽GEO / Unicorn GEO
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
<!-- ARIS-GEO:COMPILED:END -->
