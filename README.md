<!-- ARIS-GEO:HANDWRITTEN:START -->
# ARIS-GEO

一份以中国市场为主、海外产品为参照的 GEO 监测采购与实施研究。

> **我觉得在精不在多，列出来了100个甚至一千个烂产品不如精选出来真正的有效的能帮助各类用户在各种场景下解决问题的产品。**

本版截至 **2026-07-31**。公开报告只展示 7 个唯一对象：4 个优先 PoC、2 个值得
观察、1 个研究参考；同一个优秀产品可以覆盖多个用户场景，不为填表拼凑产品。

完整候选池包含 112 个对象，19 个深度档案提供字段级证据。它们保留在 `wiki/` 供
研究、去重和未来补证，但**研究长名单不等于推荐**，不会再渲染成公开产品表。

## 最终决策报告

主要交付物是
**[GEO监测产品精选报告](docs/FINAL_REPORT.md)**。它说明为什么过去筛不出优秀产品，
给出商业与开源项目的不同硬门槛，并按场景精选真正值得 PoC 的候选。

## 结论先行

1. **优先 PoC只有4个：** 透镜GEO、南云GEO、百原GEO、GEOly。
2. **透镜GEO因解决审计问题入选：** 中立账号、国内引擎和完整录屏比功能菜单更重要。
3. **当前没有足够证据的生产级开源推荐：** Aperture只列为值得观察，GEO论文只作研究参考。
4. **国内移动真机监测仍是能力空白：** 不用证据不足的产品填补表格。
5. **监测是测量系统，不是优化本身：** “写什么、发哪里”必须用内容×渠道实验验证。
6. **精选名单上限为8个唯一对象：** 新产品只有解决现有精选无法解决的问题才能加入。

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

`wiki/shortlist.json` 是公开精选层；`wiki/market-map.json` 是内部候选池；
`build_publication.py` 生成短摘录、哈希和 profile。

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
