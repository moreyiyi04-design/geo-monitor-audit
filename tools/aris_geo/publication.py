from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .schema import EVIDENCE_KINDS
from .scoring import calculate_scores, derive_auto_risk_flags


REQUIRED_PRODUCT_FIELDS = (
    "slug",
    "name_cn",
    "name_en",
    "homepage",
    "market",
    "category",
    "delivery_form",
    "openness",
    "vendor_domains",
    "sources",
    "facts",
)
DEFAULT_RESEARCH_FACT_PATHS = (
    "measurement.capture_channel",
    "measurement.samples_per_prompt",
    "measurement.reports_confidence_interval",
    "measurement.declares_noise_floor",
    "measurement.model_version_pinning",
    "measurement.sov_formula_public",
    "mechanism.data_source",
    "pricing.has_public_pricing",
    "pricing.entry_engines",
    "pricing.entry_seats",
    "pricing.entry_prompts",
    "pricing.min_commit",
    "pricing.annual_only",
    "pricing.trial",
    "pricing.refund_terms",
    "pricing.unit_inflation_risk",
    "entity.registry_verifiable",
    "entity.team_public",
    "exit.data_export",
    "exit.history_portable",
    "exit.content_hosted_by_vendor",
    "exit.contract_lock",
    "academic_anchor.peer_reviewed",
    "academic_anchor.reproducible_experiments",
    "academic_anchor.benchmark",
)


def build_publication(repo_root: str | Path, catalog: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(repo_root)
    fetched_at = catalog.get("fetched_at")
    products = catalog.get("products")
    if not isinstance(fetched_at, str) or not fetched_at:
        raise ValueError("catalog fetched_at must be a non-empty string")
    if not isinstance(products, list):
        raise ValueError("catalog products must be a list")

    seen_slugs: set[str] = set()
    profiles: list[dict[str, Any]] = []
    for product in products:
        if not isinstance(product, dict):
            raise ValueError("catalog product must be an object")
        _require_fields(product, REQUIRED_PRODUCT_FIELDS, "product")
        slug = product["slug"]
        if not isinstance(slug, str) or not slug or Path(slug).name != slug:
            raise ValueError("invalid product slug")
        if slug in seen_slugs:
            raise ValueError(f"duplicate product slug: {slug}")
        seen_slugs.add(slug)
        profiles.append(_build_product(root, fetched_at, product))
    wiki_dir = root / "wiki"
    wiki_dir.mkdir(parents=True, exist_ok=True)
    _write_json(wiki_dir / "queue.json", [profile["slug"] for profile in profiles])
    _write_json(
        wiki_dir / "sources.json",
        {
            "products": [
                {
                    "slug": product["slug"],
                    "name": product["name_en"],
                    "market": product["market"],
                    "category": product["category"],
                    "openness": product["openness"],
                    "urls": [
                        {"url": source["url"], "kind": source["kind"]}
                        for source in product["sources"]
                    ],
                    **_repo_locator(product["homepage"]),
                }
                for product in products
            ]
        },
    )
    return profiles


def _build_product(root: Path, fetched_at: str, product: dict[str, Any]) -> dict[str, Any]:
    slug = product["slug"]
    raw_dir = root / "wiki" / "raw" / slug
    products_dir = root / "wiki" / "products"
    raw_dir.mkdir(parents=True, exist_ok=True)
    products_dir.mkdir(parents=True, exist_ok=True)

    evidence = _write_evidence(raw_dir, slug, fetched_at, product["sources"])
    source_ids = {record["id"] for record in evidence}
    homepage = product["homepage"]
    vendor_domains = list(dict.fromkeys(product["vendor_domains"]))

    profile: dict[str, Any] = {
        "schema_version": "v1",
        "slug": slug,
        "name_cn": _stated(product["name_cn"], ["e1"]),
        "name_en": _stated(product["name_en"], ["e1"]),
        "homepage": _stated(homepage, ["e1"]),
        "vendor_domains": [domain for domain in vendor_domains if domain],
        "market": product["market"],
        "category": product["category"],
        "delivery_form": _stated(product["delivery_form"], ["e1"]),
        "openness": product["openness"],
    }
    facts = product["facts"]
    if not isinstance(facts, dict):
        raise ValueError(f"{slug}: facts must be an object")
    for field_path in DEFAULT_RESEARCH_FACT_PATHS:
        _set_dotted(profile, field_path, {"v": None, "src": [], "conf": "unknown"})
    for field_path, envelope in facts.items():
        _validate_fact(slug, field_path, envelope, source_ids)
        _set_dotted(profile, field_path, envelope)

    profile["evidence"] = evidence
    profile["effect_claims"] = product.get("effect_claims", [])
    profile["case_studies"] = product.get("case_studies", [])
    if "academic_anchor" not in profile and product.get("academic_anchor"):
        profile["academic_anchor"] = product["academic_anchor"]
    profile["oss_health"] = _normalize_oss_health(product.get("oss_health"))
    profile["unknowns"] = sorted(_unknown_paths(profile))
    profile["unresolved"] = product.get("unresolved", [])
    profile["observations"] = product.get("observations", [])
    profile["scores"] = calculate_scores(profile)
    profile["risk_flags"] = derive_auto_risk_flags(profile)
    profile["audit"] = {
        "rounds": 0,
        "personas": ["human-curated-public-source-catalog"],
        "usage_tokens": {},
        "generated_at": fetched_at,
    }

    destination = products_dir / f"{slug}.json"
    destination.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return profile


def _write_evidence(
    raw_dir: Path,
    slug: str,
    fetched_at: str,
    sources: Any,
) -> list[dict[str, Any]]:
    if not isinstance(sources, list) or not sources:
        raise ValueError(f"{slug}: sources must be a non-empty list")
    evidence: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError(f"{slug}: source must be an object")
        _require_fields(source, ("id", "url", "kind", "excerpt"), f"{slug} source")
        source_id = source["id"]
        if not isinstance(source_id, str) or not source_id:
            raise ValueError(f"{slug}: invalid source id")
        if source_id in seen_ids:
            raise ValueError(f"{slug}: duplicate source id: {source_id}")
        seen_ids.add(source_id)
        if source["kind"] not in EVIDENCE_KINDS:
            raise ValueError(f"{slug}: invalid evidence kind: {source['kind']}")
        excerpt = source["excerpt"]
        if not isinstance(excerpt, str) or not excerpt.strip():
            raise ValueError(f"{slug}: source excerpt must be non-empty")
        excerpt_path = raw_dir / f"{source_id}.txt"
        excerpt_path.write_text(excerpt.strip() + "\n", encoding="utf-8")
        evidence.append(
            {
                "id": source_id,
                "url": source["url"],
                "kind": source["kind"],
                "fetched_at": fetched_at,
                "sha256": hashlib.sha256(excerpt_path.read_bytes()).hexdigest(),
                "excerpt_path": f"wiki/raw/{slug}/{source_id}.txt",
                "paid_placement_suspected": bool(source.get("paid_placement_suspected", False)),
            }
        )
    return evidence


def _validate_fact(
    slug: str,
    field_path: Any,
    envelope: Any,
    source_ids: set[str],
) -> None:
    if not isinstance(field_path, str) or not field_path:
        raise ValueError(f"{slug}: fact path must be a non-empty string")
    if not isinstance(envelope, dict) or not {"v", "src", "conf"} <= set(envelope):
        raise ValueError(f"{slug}: fact {field_path} must be an envelope")
    for source_id in envelope["src"]:
        if source_id not in source_ids:
            raise ValueError(f"{slug}: {field_path} references unknown source id: {source_id}")


def _set_dotted(target: dict[str, Any], field_path: str, value: Any) -> None:
    parts = field_path.split(".")
    cursor = target
    for part in parts[:-1]:
        existing = cursor.setdefault(part, {})
        if not isinstance(existing, dict):
            raise ValueError(f"fact path collides with scalar: {field_path}")
        cursor = existing
    cursor[parts[-1]] = value


def _unknown_paths(profile: dict[str, Any]) -> list[str]:
    paths: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict) and {"v", "src", "conf"} <= set(node):
            if node.get("conf") == "unknown":
                paths.append(path)
            return
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"evidence", "oss_health", "scores", "risk_flags", "audit"}:
                    continue
                walk(value, f"{path}.{key}" if path else key)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(profile, "")
    return paths


def _normalize_oss_health(value: Any) -> dict[str, Any]:
    defaults = {
        "stars": 0,
        "created_at": None,
        "age_months": 0,
        "stars_per_month": 0,
        "contributors_12mo": 0,
        "commits_90d": 0,
        "last_release": None,
        "releases": 0,
        "tests_cover_own_logic": False,
        "license_spdx": "Proprietary",
        "license_absent": False,
        "commercial_restricted": False,
        "self_described_demo": False,
        "description_near_duplicate_of": [],
        "absolutist_claim_in_name": False,
        "upstream_vendor_confusable_name": False,
    }
    if value is None:
        return defaults
    if not isinstance(value, dict):
        raise ValueError("oss_health must be an object")
    defaults.update(value)
    return defaults


def _stated(value: Any, source_ids: list[str]) -> dict[str, Any]:
    return {"v": value, "src": source_ids, "conf": "stated"}


def _require_fields(value: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if field not in value]
    if missing:
        raise ValueError(f"{label} missing required fields: {', '.join(missing)}")


def _repo_locator(homepage: Any) -> dict[str, str]:
    if not isinstance(homepage, str) or not homepage.startswith("https://github.com/"):
        return {}
    path = homepage.removeprefix("https://github.com/").strip("/")
    if len(path.split("/")) != 2:
        return {}
    return {"repo": path}


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
