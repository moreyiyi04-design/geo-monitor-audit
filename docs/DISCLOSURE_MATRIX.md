<!-- ARIS-GEO:DISCLOSURE:START -->
# 披露率矩阵：19 家 GEO 监测产品实际公开了什么

在 19 份证据化产品档案上逐字段统计**公开材料能否确认该字段**。「已披露」表示该字段在档案中挂有至少一个证据 id；「未披露」表示公开材料不支持该字段，**不表示该能力不存在**。

这张表由 `python3 tools/disclosure_matrix.py` 从 `wiki/products/*.json` 直接重算，任何人可复现；证据快照带 SHA-256，篡改会被 `tools/verify_evidence.py --strict` 拒绝。

## 全行业空白

下列字段在 19 份档案中**没有任何一家**能从公开材料确认：

- `measurement.samples_per_prompt`
- `measurement.declares_noise_floor`
- `measurement.reports_confidence_interval`
- `measurement.model_version_pinning`
- `pricing.entry_seats`
- `exit.history_portable`
- `exit.contract_lock`
- `entity.registry_verifiable`
- `entity.team_public`

这意味着采购方无法从公开材料判断这些产品的采样次数、误差、版本治理、历史数据可迁移性与主体可核实性。**这些必须在 PoC 现场验收，不能靠官网。**

## 测量严谨性

| 字段 | 已披露 / 覆盖 | 披露率 |
| --- | --- | --- |
| `capture_channel` | 6 / 19 | 32% |
| `sampling_frequency` | 9 / 9 | 100% |
| `samples_per_prompt` | 0 / 19 | 0% |
| `sov_formula_public` | 3 / 19 | 16% |
| `declares_noise_floor` | 0 / 19 | 0% |
| `reports_confidence_interval` | 0 / 19 | 0% |
| `model_version_pinning` | 0 / 19 | 0% |

## 价格透明

| 字段 | 已披露 / 覆盖 | 披露率 |
| --- | --- | --- |
| `has_public_pricing` | 15 / 19 | 79% |
| `trial` | 9 / 19 | 47% |
| `entry_engines` | 6 / 19 | 32% |
| `entry_prompts` | 5 / 19 | 26% |
| `entry_seats` | 0 / 19 | 0% |
| `min_commit` | 5 / 19 | 26% |
| `annual_only` | 10 / 19 | 53% |
| `refund_terms` | 1 / 19 | 5% |
| `unit_inflation_risk` | 1 / 19 | 5% |

## 退出与可迁移

| 字段 | 已披露 / 覆盖 | 披露率 |
| --- | --- | --- |
| `data_export` | 10 / 19 | 53% |
| `history_portable` | 0 / 19 | 0% |
| `contract_lock` | 0 / 19 | 0% |
| `content_hosted_by_vendor` | 5 / 19 | 26% |

## 主体可核实

| 字段 | 已披露 / 覆盖 | 披露率 |
| --- | --- | --- |
| `registry_verifiable` | 0 / 19 | 0% |
| `team_public` | 0 / 19 | 0% |

## 研究锚点

| 字段 | 已披露 / 覆盖 | 披露率 |
| --- | --- | --- |
| `peer_reviewed` | 1 / 19 | 5% |
| `reproducible_experiments` | 2 / 19 | 11% |
| `benchmark` | 2 / 19 | 11% |

## 怎么用这张表

披露率低的字段不是「次要指标」，而是**供应商普遍回避的地方**——恰恰是 PoC 要重点验收的。把披露率 0% 的字段直接抄进你的 PoC 验收清单，要求供应商现场给出答案并留证。
<!-- ARIS-GEO:DISCLOSURE:END -->
