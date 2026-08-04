"""命令行入口：在已安装的包上直接跑披露率审计、分数重算与证据校验。

包内随附 19 份证据化产品档案（`wiki/`），因此 `pip install` 之后无需克隆仓库即可运行：

    geo-monitor-audit disclosure          # 逐字段披露率矩阵
    geo-monitor-audit disclosure --json   # 原始计数
    geo-monitor-audit verify              # 校验证据快照的 sha256 与来源完整性
    geo-monitor-audit score               # 从字段重算分数并与档案比对

传 `--repo <路径>` 可改为在某个仓库检出目录上运行，用于本地开发。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .compiler import find_repo_root
from .evidence import validate_profile
from .schema import iter_envelopes
from .scoring import calculate_scores

__all__ = ["bundled_root", "resolve_root", "main"]


def bundled_root() -> Path | None:
    """随包分发的数据根目录（其下有 `wiki/products/`）；源码检出时不存在。"""
    candidate = Path(__file__).resolve().parent / "_bundled"
    return candidate if (candidate / "wiki" / "products").is_dir() else None


def resolve_root(explicit: str | None) -> Path:
    """定位数据根目录：显式指定 > 当前仓库检出 > 包内随附副本。

    返回的目录下必须有 `wiki/products/`。找不到时抛 SystemExit 并说明原因，
    而不是静默用空数据集算出一张全 0 的表。
    """
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not (root / "wiki" / "products").is_dir():
            raise SystemExit(f"--repo 指向的目录下没有 wiki/products/：{root}")
        return root

    try:
        root = find_repo_root(Path.cwd())
        if (root / "wiki" / "products").is_dir():
            return root
    except Exception:  # noqa: BLE001 — 未在仓库内运行是正常情况，回退到包内数据
        pass

    bundled = bundled_root()
    if bundled is None:
        raise SystemExit(
            "找不到 wiki/products/。请在仓库检出目录内运行，或用 --repo 指定路径。"
        )
    return bundled


def _load_profiles(root: Path) -> dict[str, dict]:
    from .disclosure import load_profiles

    try:
        return load_profiles(root)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc


def _cmd_disclosure(args: argparse.Namespace) -> int:
    from .disclosure import compute, render

    report = compute(_load_profiles(resolve_root(args.repo)))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render(report))
    return 0


def _cmd_verify(args: argparse.Namespace) -> int:
    root = resolve_root(args.repo)
    failures = 0
    for slug, profile in sorted(_load_profiles(root).items()):
        report = validate_profile(profile, root, strict=True)
        if report.errors:
            failures += 1
            print(f"✗ {slug}")
            for err in report.errors:
                print(f"    {err}")
        else:
            n = sum(1 for _ in iter_envelopes(profile))
            print(f"✓ {slug}  {n} 个字段")
    if failures:
        print(f"\n{failures} 份档案未通过证据校验", file=sys.stderr)
        return 1
    print("\n全部通过：每个非 unknown 字段都挂着来源，每份快照的 sha256 一致")
    return 0


def _cmd_score(args: argparse.Namespace) -> int:
    root = resolve_root(args.repo)
    drift = 0
    for slug, profile in sorted(_load_profiles(root).items()):
        recomputed = calculate_scores(profile)
        stored = profile.get("scores") or {}
        if stored and stored != recomputed:
            drift += 1
            print(f"✗ {slug}  档案内分数与重算结果不一致")
            print(f"    档案: {json.dumps(stored, ensure_ascii=False, sort_keys=True)}")
            print(f"    重算: {json.dumps(recomputed, ensure_ascii=False, sort_keys=True)}")
        else:
            shown = " ".join(f"{k}={v}" for k, v in sorted(recomputed.items()))
            print(f"✓ {slug}  {shown}")
    if drift:
        print(f"\n{drift} 份档案的分数无法从字段重算得到", file=sys.stderr)
        return 1
    print("\n全部一致：分数可由 Python 从字段重算，不依赖模型给分")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geo-monitor-audit",
        description="GEO 监测平台选型审计：19 份证据化档案的逐字段披露率、证据校验与分数重算。",
    )
    parser.add_argument("--repo", help="改为在指定的仓库检出目录上运行")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("disclosure", help="逐字段披露率矩阵")
    p.add_argument("--json", action="store_true", help="输出原始计数而非渲染后的表")
    p.set_defaults(func=_cmd_disclosure)

    p = sub.add_parser("verify", help="校验证据快照的 sha256 与来源完整性")
    p.set_defaults(func=_cmd_verify)

    p = sub.add_parser("score", help="从字段重算分数并与档案内的值比对")
    p.set_defaults(func=_cmd_score)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
