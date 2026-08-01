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
    profile_list = list(profiles)
    lines = [
        f"> 数据截至 {_data_cutoff(profile_list)}",
        "> 「未披露」≠「没有」；产品级证据、分数和风险字段保留在 wiki/products/。",
        "",
    ]
    if market_map:
        lines.extend(
            [
                "### 附录：全球市场地图",
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


def _market_map_sort_key(entry: dict[str, Any]) -> tuple[str, str]:
    return (_as_text(entry.get("slug")), _as_text(entry.get("name")))


def _as_text(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip()
    return text or "—"


def _category_values(categories: Any) -> str:
    if isinstance(categories, list) and categories:
        return ", ".join(_as_text(item) for item in categories)
    return "—"


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
