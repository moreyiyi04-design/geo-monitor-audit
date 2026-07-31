from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


COMPILED_START_MARKER = "<!-- ARIS-GEO:COMPILED:START -->"
COMPILED_END_MARKER = "<!-- ARIS-GEO:COMPILED:END -->"
README_FILENAME = "README.md"
PRODUCTS_DIR = Path("wiki/products")
MARKET_MAP_FILENAME = Path("wiki/market-map.json")
MARKET_MAP_COVERAGE = frozenset({"market-map-only", "deep-profile"})


def render_compiled_block(
    profiles: Iterable[dict[str, Any]],
    market_map: Iterable[dict[str, Any]] | None = None,
) -> str:
    ordered = sorted(profiles, key=_profile_sort_key)
    lines = [
        f"> 数据截至 {_data_cutoff(ordered)}",
        "> 「未披露」≠「没有」；下表仅呈现已公开且有证据的字段。",
        "",
    ]
    if market_map:
        lines.extend(
            [
                "### 市场地图",
                "| 产品 | 市场 | 类别 | 形态 | 开放性 | 覆盖级别 | 官网 |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for entry in sorted(market_map, key=_market_map_sort_key):
            lines.append(
                "| {name} | {market} | {category} | {delivery_form} | {openness} | {coverage} | {homepage} |".format(
                    name=_as_text(entry.get("name")),
                    market=_as_text(entry.get("market")),
                    category=_category_values(entry.get("category")),
                    delivery_form=_as_text(entry.get("delivery_form")),
                    openness=_as_text(entry.get("openness")),
                    coverage=_as_text(entry.get("coverage")),
                    homepage=_as_text(entry.get("homepage")),
                )
            )
        lines.append("")

    lines.extend(
        [
            "### 选型矩阵",
            "| 产品 | slug | 市场 | 形态 | 开放性 | 核心类别 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for profile in ordered:
        lines.append(
            "| {name} | {slug} | {market} | {delivery_form} | {openness} | {category} |".format(
                name=_display_name(profile),
                slug=_as_text(profile.get("slug")),
                market=_as_text(profile.get("market")),
                delivery_form=_field_value(profile, "delivery_form"),
                openness=_as_text(profile.get("openness")),
                category=_primary_category(profile),
            )
        )

    lines.extend(
        [
            "",
            "### 分数",
            "| 产品 | transparency | verifiability | lock_in_risk | measurement_rigor | oss_health |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for profile in ordered:
        scores = profile.get("scores", {})
        lines.append(
            "| {name} | {transparency} | {verifiability} | {lock_in_risk} | {measurement_rigor} | {oss_health} |".format(
                name=_display_name(profile),
                transparency=_score_value(scores, "transparency"),
                verifiability=_score_value(scores, "verifiability"),
                lock_in_risk=_score_value(scores, "lock_in_risk"),
                measurement_rigor=_score_value(scores, "measurement_rigor"),
                oss_health=_score_value(scores, "oss_health"),
            )
        )

    lines.extend(
        [
            "",
            "### 产品档案表",
            "| 产品 | 官网 | 类别 | 公开定价 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for profile in ordered:
        lines.append(
            "| {name} | {homepage} | {categories} | {pricing} |".format(
                name=_display_name(profile),
                homepage=_field_value(profile, "homepage"),
                categories=_category_list(profile),
                pricing=_pricing_label(profile),
            )
        )

    lines.append("")
    lines.append("### 标签清单")
    for profile in ordered:
        lines.append(f"#### {_display_name(profile)}")
        flags = _sorted_flags(profile.get("risk_flags", []))
        if not flags:
            lines.append("- 无")
            lines.append("")
            continue
        for flag in flags:
            lines.append(f"- {_flag_prefix(flag.get('tier'))} {_as_text(flag.get('flag'))}")
        lines.append("")

    return "\n".join(lines)


def replace_compiled_block(readme: str, block: str) -> str:
    start_index = _find_unique_marker(
        readme,
        COMPILED_START_MARKER,
        missing_message=f"missing compiled start marker: {COMPILED_START_MARKER}",
        duplicate_message=f"duplicate compiled start marker: {COMPILED_START_MARKER}",
    )
    end_index = _find_unique_marker(
        readme,
        COMPILED_END_MARKER,
        missing_message=f"missing compiled end marker: {COMPILED_END_MARKER}",
        duplicate_message=f"duplicate compiled end marker: {COMPILED_END_MARKER}",
    )
    if end_index < start_index:
        raise ValueError("compiled end marker occurs before start marker")

    prefix = readme[: start_index + len(COMPILED_START_MARKER)]
    suffix = readme[end_index:]
    normalized = block.rstrip("\n")
    if normalized:
        return f"{prefix}\n{normalized}\n{suffix}"
    return f"{prefix}\n{suffix}"


def _find_unique_marker(
    readme: str,
    marker: str,
    *,
    missing_message: str,
    duplicate_message: str,
) -> int:
    first_index = readme.find(marker)
    if first_index == -1:
        raise ValueError(missing_message)

    second_index = readme.find(marker, first_index + len(marker))
    if second_index != -1:
        raise ValueError(duplicate_message)

    return first_index


def load_profiles(repo_root: Path) -> list[dict[str, Any]]:
    profiles_dir = repo_root / PRODUCTS_DIR
    paths = sorted(path for path in profiles_dir.glob("*.json") if path.is_file())
    profiles: list[dict[str, Any]] = []
    for path in paths:
        profiles.append(json.loads(path.read_text(encoding="utf-8")))
    return profiles


def load_market_map(repo_root: Path) -> list[dict[str, Any]]:
    market_map_path = repo_root / MARKET_MAP_FILENAME
    if not market_map_path.exists():
        return []
    payload = json.loads(market_map_path.read_text(encoding="utf-8"))
    products = payload.get("products")
    if not isinstance(products, list):
        raise ValueError("market-map products must be a list")

    entries: list[dict[str, Any]] = []
    seen_slugs: set[str] = set()
    for item in products:
        if not isinstance(item, dict):
            raise ValueError("market-map products must contain objects")
        slug = _as_text(item.get("slug"))
        if slug in seen_slugs:
            raise ValueError(f"duplicate market-map slug: {slug}")
        seen_slugs.add(slug)

        coverage = _as_text(item.get("coverage"))
        if coverage not in MARKET_MAP_COVERAGE:
            raise ValueError(f"invalid market-map coverage for {slug}: {coverage}")
        entries.append(item)
    return entries


def compile_readme(repo_root: Path) -> tuple[str, str]:
    readme_path = repo_root / README_FILENAME
    readme = readme_path.read_text(encoding="utf-8")
    block = render_compiled_block(load_profiles(repo_root), load_market_map(repo_root))
    return readme, replace_compiled_block(readme, block)


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
        if (candidate / README_FILENAME).exists() and (candidate / PRODUCTS_DIR).is_dir():
            return candidate
    raise FileNotFoundError(f"could not find repository root from {current}")


def _profile_sort_key(profile: dict[str, Any]) -> tuple[str, str]:
    return (_as_text(profile.get("slug")), _display_name(profile))


def _display_name(profile: dict[str, Any]) -> str:
    name_cn = _field_value(profile, "name_cn")
    name_en = _field_value(profile, "name_en")
    if name_cn != "—" and name_en != "—":
        return f"{name_cn} / {name_en}"
    if name_cn != "—":
        return name_cn
    if name_en != "—":
        return name_en
    return _as_text(profile.get("slug"))


def _market_map_sort_key(entry: dict[str, Any]) -> tuple[str, str]:
    return (_as_text(entry.get("slug")), _as_text(entry.get("name")))


def _field_value(profile: dict[str, Any], field: str) -> str:
    return _as_text(_unwrap(profile.get(field)))


def _unwrap(value: Any) -> Any:
    if isinstance(value, dict) and {"v", "src", "conf"} <= set(value):
        return value.get("v")
    return value


def _as_text(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip()
    return text or "—"


def _primary_category(profile: dict[str, Any]) -> str:
    categories = profile.get("category")
    if isinstance(categories, list) and categories:
        return ", ".join(_as_text(item) for item in categories[:1])
    return "—"


def _category_list(profile: dict[str, Any]) -> str:
    categories = profile.get("category")
    if isinstance(categories, list) and categories:
        return ", ".join(_as_text(item) for item in categories)
    return "—"


def _category_values(categories: Any) -> str:
    if isinstance(categories, list) and categories:
        return ", ".join(_as_text(item) for item in categories)
    return "—"


def _pricing_label(profile: dict[str, Any]) -> str:
    if "学术参考实现" in (profile.get("category") or []):
        return "不适用"
    if profile.get("openness") == "open-source":
        return "开源 / 自托管"
    pricing = profile.get("pricing")
    if not isinstance(pricing, dict):
        return "—"
    has_public_pricing = _unwrap(pricing.get("has_public_pricing"))
    if has_public_pricing is True:
        return "已公开"
    if has_public_pricing is False:
        return "未公开"
    return "—"


def _score_value(scores: dict[str, Any], key: str) -> str:
    return _as_text(scores.get(key))


def _sorted_flags(flags: Any) -> list[dict[str, Any]]:
    if not isinstance(flags, list):
        return []
    items = [flag for flag in flags if isinstance(flag, dict)]
    return sorted(
        items,
        key=lambda flag: (
            _tier_rank(flag.get("tier")),
            _as_text(flag.get("flag")),
            _as_text(flag.get("origin")),
        ),
    )


def _tier_rank(tier: Any) -> int:
    if tier == "yellow":
        return 0
    if tier == "orange":
        return 1
    return 2


def _flag_prefix(tier: Any) -> str:
    if tier == "yellow":
        return "🟡"
    if tier == "orange":
        return "🟠"
    return "•"


def _data_cutoff(profiles: list[dict[str, Any]]) -> str:
    dates: list[str] = []
    for profile in profiles:
        evidence = profile.get("evidence")
        if not isinstance(evidence, list):
            continue
        for record in evidence:
            if isinstance(record, dict):
                fetched_at = record.get("fetched_at")
                if isinstance(fetched_at, str) and fetched_at:
                    dates.append(fetched_at)
    if not dates:
        return "unknown"
    return max(dates)
