"""披露率矩阵的计算与渲染。

报告的核心断言是「多数 GEO 监测厂商不公开采购方需要的字段」。这个断言只有被
**数出来**而不是被声称，才有价值——所以这里读 `wiki/products/*.json`，逐字段
统计有多少份档案挂着有来源的值，有多少是 `unknown`。

逻辑放在包内，命令行入口（`tools/disclosure_matrix.py` 与 `geo-monitor-audit
disclosure`）共用同一份实现，避免两处渲染结果漂移导致 CI 门与已安装包给出
不同的数字。
"""

from __future__ import annotations

import json
from pathlib import Path

__all__ = [
    "GROUPS",
    "MARKER_END",
    "MARKER_START",
    "compute",
    "load_profiles",
    "render",
    "wrap",
]

# 字段分组沿用报告组织采购问题的方式，使矩阵能与六维评估框架并排阅读。
GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "measurement",
        "测量严谨性",
        (
            "measurement.capture_channel",
            "measurement.sampling_frequency",
            "measurement.samples_per_prompt",
            "measurement.sov_formula_public",
            "measurement.declares_noise_floor",
            "measurement.reports_confidence_interval",
            "measurement.model_version_pinning",
        ),
    ),
    (
        "pricing",
        "价格透明",
        (
            "pricing.has_public_pricing",
            "pricing.trial",
            "pricing.entry_engines",
            "pricing.entry_prompts",
            "pricing.entry_seats",
            "pricing.min_commit",
            "pricing.annual_only",
            "pricing.refund_terms",
            "pricing.unit_inflation_risk",
        ),
    ),
    (
        "exit",
        "退出与可迁移",
        (
            "exit.data_export",
            "exit.history_portable",
            "exit.contract_lock",
            "exit.content_hosted_by_vendor",
        ),
    ),
    (
        "entity",
        "主体可核实",
        ("entity.registry_verifiable", "entity.team_public"),
    ),
    (
        "academic_anchor",
        "研究锚点",
        (
            "academic_anchor.peer_reviewed",
            "academic_anchor.reproducible_experiments",
            "academic_anchor.benchmark",
        ),
    ),
)

MARKER_START = "<!-- ARIS-GEO:DISCLOSURE:START -->"
MARKER_END = "<!-- ARIS-GEO:DISCLOSURE:END -->"


def _envelope(profile: dict, dotted: str) -> dict | None:
    node: object = profile
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node if isinstance(node, dict) and "conf" in node else None


def load_profiles(repo_root: Path) -> dict[str, dict]:
    directory = repo_root / "wiki" / "products"
    profiles: dict[str, dict] = {}
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        profiles[payload.get("slug") or path.stem] = payload
    if not profiles:
        raise FileNotFoundError(f"no product dossiers under {directory}")
    return profiles


def compute(profiles: dict[str, dict]) -> dict:
    total = len(profiles)
    groups = []
    for group_key, group_label, fields in GROUPS:
        rows = []
        for dotted in fields:
            present = 0
            disclosed = 0
            disclosing = []
            for slug, profile in profiles.items():
                envelope = _envelope(profile, dotted)
                if envelope is None:
                    continue
                present += 1
                if envelope.get("conf") != "unknown":
                    disclosed += 1
                    disclosing.append(slug)
            rows.append(
                {
                    "field": dotted,
                    "leaf": dotted.split(".")[-1],
                    "present": present,
                    "disclosed": disclosed,
                    "rate": (disclosed / present) if present else 0.0,
                    "disclosing": disclosing,
                }
            )
        groups.append({"key": group_key, "label": group_label, "fields": rows})
    blanks = [
        row["field"]
        for group in groups
        for row in group["fields"]
        if row["present"] and row["disclosed"] == 0
    ]
    return {"n_products": total, "groups": groups, "industry_blanks": blanks}


def render(report: dict) -> str:
    total = report["n_products"]
    lines: list[str] = []
    lines.append("# 披露率矩阵：19 家 GEO 监测产品实际公开了什么")
    lines.append("")
    lines.append(
        f"在 {total} 份证据化产品档案上逐字段统计**公开材料能否确认该字段**。"
        "「已披露」表示该字段在档案中挂有至少一个证据 id；「未披露」表示公开材料"
        "不支持该字段，**不表示该能力不存在**。"
    )
    lines.append("")
    lines.append(
        "这张表由 `python3 tools/disclosure_matrix.py` 从 `wiki/products/*.json` 直接重算，"
        "任何人可复现；证据快照带 SHA-256，篡改会被 `tools/verify_evidence.py --strict` 拒绝。"
    )
    lines.append("")

    blanks = report["industry_blanks"]
    if blanks:
        lines.append("## 全行业空白")
        lines.append("")
        lines.append(f"下列字段在 {total} 份档案中**没有任何一家**能从公开材料确认：")
        lines.append("")
        for field in blanks:
            lines.append(f"- `{field}`")
        lines.append("")
        lines.append(
            "这意味着采购方无法从公开材料判断这些产品的采样次数、误差、版本治理、"
            "历史数据可迁移性与主体可核实性。**这些必须在 PoC 现场验收，不能靠官网。**"
        )
        lines.append("")

    for group in report["groups"]:
        lines.append(f"## {group['label']}")
        lines.append("")
        lines.append("| 字段 | 已披露 / 覆盖 | 披露率 |")
        lines.append("| --- | --- | --- |")
        for row in group["fields"]:
            lines.append(
                f"| `{row['leaf']}` | {row['disclosed']} / {row['present']} | {row['rate'] * 100:.0f}% |"
            )
        lines.append("")

    lines.append("## 怎么用这张表")
    lines.append("")
    lines.append(
        "披露率低的字段不是「次要指标」，而是**供应商普遍回避的地方**——恰恰是 PoC 要重点验收的。"
        "把披露率 0% 的字段直接抄进你的 PoC 验收清单，要求供应商现场给出答案并留证。"
    )
    lines.append("")
    return "\n".join(lines)


def wrap(body: str) -> str:
    return f"{MARKER_START}\n{body.rstrip()}\n{MARKER_END}\n"
