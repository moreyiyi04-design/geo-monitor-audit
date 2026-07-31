<!-- ARIS-GEO:HANDWRITTEN:START -->
# ARIS-GEO

一份带来源、证据等级、未知项和可复算分数的 GEO / AEO 工具横向报告。

本版截至 **2026-07-31**，收录 14 个真实对象：

- 4 个海外 SaaS：Profound、Scrunch AI、OtterlyAI、Rankscale
- 3 个国内 SaaS：GEO AI搜索优化、独角兽GEO、GTark
- 5 个开源工具或 Agent Skill
- 2 个学术参考实现

这不是总榜。不同产品解决的问题不同，下面只发布分维度结果，不把它们压成一个
“第一名”。测试所用的合成 Profound 样本仍保留在 `tests/fixtures/`，但不参与报告。

## 结论先行

1. **测量口径仍是市场最大短板。** 公开材料中，Profound 与独角兽GEO明确声称使用
   浏览器端采集；GTark说明记录真实平台对话并重复采样。14 个对象均未公开可核验的
   每 prompt 样本数、置信区间和噪声下限完整组合。
2. **公开定价不等于可横向比价。** 有的平台按 prompt，有的按问题/关键词，有的按
   credit 和引擎次数计费；报告保留原始单位，不用伪精确换算制造可比性。
3. **第一方效果数字不能当独立证据。** Scrunch 的 4x 与 GTark 的 32%→94.81%
   均按 D 级处理；GEO 论文的“最高 40%”有公开论文与实验基准，但仍只代表其设定。
4. **开源不自动等于成熟。** 本版把许可证、贡献者、近期提交、发布和业务测试分开
   记录；星标不进入总分，也不作为产品质量代理。
5. **国内样本的优化闭环更靠近内容投放。** 独角兽GEO公开描述监测后直接连接媒体
   投稿；这类机制与海外纯监测平台不同，采购时应额外审查品牌安全与平台规则风险。

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

### 选型矩阵
| 产品 | slug | 市场 | 形态 | 开放性 | 核心类别 |
| --- | --- | --- | --- | --- | --- |
| Aperture / Aperture | aperture | overseas | Self-hosted web application | open-source | 监测/可见性追踪 |
| E-GEO 电商测试床 / E-GEO: A Testbed for Generative Engine Optimization in E-Commerce | e_geo_testbed | overseas | Research paper and testbed | source-available | 学术参考实现 |
| GEO/AEO Tracker / GEO/AEO Tracker | geo_aeo_tracker | overseas | Self-hosted web application | open-source | 监测/可见性追踪 |
| 生成式引擎优化（GEO） / GEO: Generative Engine Optimization | geo_generative_engine_optimization | overseas | Research paper and benchmark | source-available | 学术参考实现 |
| GEO Optimizer Skill / GEO Optimizer Skill | geo_optimizer_skill | overseas | Agent skill and audit toolkit | open-source | agent-skill/prompt-pack |
| GEO AI搜索优化 / GEO AI Search Optimization | geo_tool_cn | domestic | SaaS | closed | 一体化平台 |
| GEO Skills / GEO Skills | geoskills | overseas | Agent skill suite | open-source | agent-skill/prompt-pack |
| GTark / GTark | gtark | domestic | SaaS | closed | 一体化平台 |
| OtterlyAI / OtterlyAI | otterlyai | overseas | SaaS | closed | 监测/可见性追踪 |
| Profound / Profound | profound | overseas | SaaS | closed | 一体化平台 |
| Rankscale / Rankscale | rankscale | overseas | SaaS | closed | 监测/可见性追踪 |
| Scrunch AI / Scrunch AI | scrunch_ai | overseas | SaaS | closed | 一体化平台 |
| SEO & GEO Skills Library / SEO & GEO Skills Library | seo_geo_claude_skills | overseas | Agent skill library | open-source | agent-skill/prompt-pack |
| 独角兽GEO / Unicorn GEO | unicorn_geo | domestic | SaaS | closed | 一体化平台 |

### 分数
| 产品 | transparency | verifiability | lock_in_risk | measurement_rigor | oss_health |
| --- | --- | --- | --- | --- | --- |
| Aperture / Aperture | 2 | 0 | 0 | 0 | 3 |
| E-GEO 电商测试床 / E-GEO: A Testbed for Generative Engine Optimization in E-Commerce | 2 | 0 | 0 | 0 | 3 |
| GEO/AEO Tracker / GEO/AEO Tracker | 2 | 0 | 0 | 0 | 2 |
| 生成式引擎优化（GEO） / GEO: Generative Engine Optimization | 2 | 5 | 0 | 0 | 5 |
| GEO Optimizer Skill / GEO Optimizer Skill | 2 | 0 | 0 | 0 | 3 |
| GEO AI搜索优化 / GEO AI Search Optimization | 2 | 0 | 0 | 0 | 0 |
| GEO Skills / GEO Skills | 2 | 0 | 0 | 0 | 3 |
| GTark / GTark | 4 | 1 | 0 | 1 | 0 |
| OtterlyAI / OtterlyAI | 2 | 0 | 0 | 0 | 0 |
| Profound / Profound | 3 | 0 | 2 | 2 | 0 |
| Rankscale / Rankscale | 2 | 0 | 0 | 0 | 0 |
| Scrunch AI / Scrunch AI | 1 | 1 | 0 | 0 | 0 |
| SEO & GEO Skills Library / SEO & GEO Skills Library | 2 | 0 | 0 | 0 | 4 |
| 独角兽GEO / Unicorn GEO | 3 | 0 | 0 | 1 | 0 |

### 产品档案表
| 产品 | 官网 | 类别 | 公开定价 |
| --- | --- | --- | --- |
| Aperture / Aperture | https://github.com/anyin-ai/aperture | 监测/可见性追踪 | 开源 / 自托管 |
| E-GEO 电商测试床 / E-GEO: A Testbed for Generative Engine Optimization in E-Commerce | https://arxiv.org/abs/2511.20867 | 学术参考实现 | 不适用 |
| GEO/AEO Tracker / GEO/AEO Tracker | https://github.com/danishashko/geo-aeo-tracker | 监测/可见性追踪 | 开源 / 自托管 |
| 生成式引擎优化（GEO） / GEO: Generative Engine Optimization | https://arxiv.org/abs/2311.09735 | 学术参考实现 | 不适用 |
| GEO Optimizer Skill / GEO Optimizer Skill | https://github.com/Auriti-Labs/geo-optimizer-skill | agent-skill/prompt-pack | 开源 / 自托管 |
| GEO AI搜索优化 / GEO AI Search Optimization | https://www.geo-tool.cn/ | 一体化平台, 监测/可见性追踪 | 已公开 |
| GEO Skills / GEO Skills | https://github.com/Cognitic-Labs/geoskills | agent-skill/prompt-pack | 开源 / 自托管 |
| GTark / GTark | https://www.gtark.com/ | 一体化平台, 监测/可见性追踪 | 已公开 |
| OtterlyAI / OtterlyAI | https://otterly.ai/ | 监测/可见性追踪 | 已公开 |
| Profound / Profound | https://www.tryprofound.com/ | 一体化平台, 监测/可见性追踪 | 已公开 |
| Rankscale / Rankscale | https://rankscale.ai/ | 监测/可见性追踪 | 已公开 |
| Scrunch AI / Scrunch AI | https://scrunch.com/ | 一体化平台, 监测/可见性追踪 | — |
| SEO & GEO Skills Library / SEO & GEO Skills Library | https://github.com/aaron-he-zhu/seo-geo-claude-skills | agent-skill/prompt-pack | 开源 / 自托管 |
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

#### 独角兽GEO / Unicorn GEO
- 🟡 不报告置信区间或误差范围
- 🟡 入门档席位数未披露
- 🟡 可见性份额口径未公开
- 🟡 团队信息未公开 / 客户案例未能交叉验证
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟡 模型版本未钉定,时间序列可能断裂
<!-- ARIS-GEO:COMPILED:END -->
