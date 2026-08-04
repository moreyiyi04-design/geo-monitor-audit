"""Compute the disclosure matrix: how many of the profiled products actually
publish each field.

The report's core claim is that most GEO monitoring vendors do not disclose the
things a buyer needs. That claim is only worth anything if it is counted rather
than asserted, so this reads `wiki/products/*.json` and reports, per field, how
many dossiers carry a sourced value versus `unknown`.

Usage:
    python3 tools/disclosure_matrix.py              # render markdown to stdout
    python3 tools/disclosure_matrix.py --json       # machine-readable
    python3 tools/disclosure_matrix.py --write      # refresh docs/DISCLOSURE_MATRIX.md
    python3 tools/disclosure_matrix.py --check      # fail if the doc is stale
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.aris_geo.compiler import find_repo_root

DOC_RELATIVE = Path("docs/DISCLOSURE_MATRIX.md")

# Field groups follow the buyer questions the report is organised around, so the
# matrix can be read next to the six evaluation dimensions.
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


def _wrap(body: str) -> str:
    return f"{MARKER_START}\n{body.rstrip()}\n{MARKER_END}\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit the raw counts.")
    parser.add_argument("--write", action="store_true", help="Refresh the rendered doc.")
    parser.add_argument("--check", action="store_true", help="Fail if the rendered doc is stale.")
    args = parser.parse_args(argv)

    repo_root = find_repo_root()
    report = compute(load_profiles(repo_root))

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    rendered = _wrap(render(report))
    target = repo_root / DOC_RELATIVE

    if args.check:
        if not target.is_file():
            print(f"{DOC_RELATIVE} is missing", file=sys.stderr)
            return 1
        if target.read_text(encoding="utf-8") != rendered:
            print(f"{DOC_RELATIVE} is stale", file=sys.stderr)
            return 1
        return 0

    if args.write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
        return 0

    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
