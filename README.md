<!-- ARIS-GEO:HANDWRITTEN:START -->
# ARIS-GEO

This repository currently commits a **synthetic offline fixture** for `profound`.
Every committed `wiki/` record, excerpt, score, flag, and README compiled block
in this branch is synthetic test data for deterministic validation only. It is
not live research, not a product finding, and not a ranking.

## Requirements

- Python 3.11+
- Optional ARIS-Code v0.4.21+ for live execution (`v0.4.22+` recommended)

## Offline Verification

```bash
python3 -m unittest discover -s tests -v
python3 tools/verify_evidence.py --strict
python3 tools/score.py --check
python3 tools/compile_readme.py --check
```

To refresh committed deterministic outputs:

```bash
python3 tools/score.py
python3 tools/compile_readme.py
```

## Optional Live Run

Live execution is intentionally separate from the committed offline fixture.
The live smoke is not run here, and no credentials or ARIS installation are
bundled with this repository.

```bash
export TAVILY_API_KEY=replace-me
export EXECUTOR_API_KEY=replace-me
# or: export OPENAI_API_KEY=replace-me
export ARIS_DISABLE_KEYCHAIN=1

python3 tools/geo_loop.py --limit 1
python3 tools/geo_loop.py --refresh-stale 90
```

## Security

Do not commit API keys. Keep secrets in environment variables only. The verify
workflow runs without repository secrets or network access beyond action setup.

See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for scope, limitations, and why
the committed Profound profile is explicitly synthetic.
<!-- ARIS-GEO:HANDWRITTEN:END -->

<!-- ARIS-GEO:COMPILED:START -->
> 数据截至 2026-07-31
> 「未披露」≠「没有」；下表仅呈现已公开且有证据的字段。

### 选型矩阵
| 产品 | slug | 市场 | 形态 | 开放性 | 核心类别 |
| --- | --- | --- | --- | --- | --- |
| Profound（合成离线样本） / Profound (Synthetic Offline Fixture) | profound | overseas | Synthetic SaaS fixture | closed | 监测/可见性追踪 |

### 分数
| 产品 | transparency | verifiability | lock_in_risk | measurement_rigor | oss_health |
| --- | --- | --- | --- | --- | --- |
| Profound（合成离线样本） / Profound (Synthetic Offline Fixture) | 3 | 5 | 4 | 2 | 5 |

### 产品档案表
| 产品 | 官网 | 类别 | 公开定价 |
| --- | --- | --- | --- |
| Profound（合成离线样本） / Profound (Synthetic Offline Fixture) | https://example.invalid/profound | 监测/可见性追踪 | 未公开 |

### 标签清单
#### Profound（合成离线样本） / Profound (Synthetic Offline Fixture)
- 🟡 不报告置信区间或误差范围
- 🟡 入门档仅覆盖单一引擎
- 🟡 无公开定价 / 仅年付 / 无试用 / 退款条款未公开
- 🟡 未声明测量噪声下限
- 🟡 未披露每 prompt 采样次数
- 🟠 无数据导出 / 最低合约期 > 6 个月
- 🟠 计价单位随监测范围膨胀
<!-- ARIS-GEO:COMPILED:END -->
