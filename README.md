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
> 完整候选池保留在 wiki/market-map.json，仅供研究与审计，不构成公开推荐。
<!-- ARIS-GEO:COMPILED:END -->
