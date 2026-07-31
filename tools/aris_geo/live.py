from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .aris import ArisResult, run_aris_phase
from .compiler import compile_readme
from .github import GitHubHealthClient
from .http import HttpRequest, HttpResponse, Transport, atomic_write_json, default_transport, utc_now_iso
from .loop import PhaseOutcome
from .state import Phase, ProductState
from .staging import stage_persona_inbox
from .tavily import TavilyClient


DEFAULT_SOURCES_PATH = Path("wiki") / "sources.json"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_TAVILY_CACHE_DIR = Path(".cache") / "tavily"
DEFAULT_GITHUB_CACHE_DIR = Path(".cache") / "github"
PATCH_ROOT_ALLOWLIST = frozenset(
    {
        "schema_version",
        "slug",
        "name_cn",
        "name_en",
        "homepage",
        "vendor_domains",
        "market",
        "category",
        "delivery_form",
        "openness",
        "measurement",
        "mechanism",
        "features",
        "effect_claims",
        "tactics",
        "pricing",
        "enterprise",
        "org_requirement",
        "exit",
        "entity",
        "case_studies",
        "academic_anchor",
        "fit",
        "unknowns",
        "unresolved",
        "observations",
    }
)


@dataclass(frozen=True)
class ManifestUrl:
    url: str
    kind: str


@dataclass(frozen=True)
class ProductSource:
    slug: str
    name: str
    market: str
    category: tuple[str, ...]
    openness: str
    urls: tuple[ManifestUrl, ...]
    repo: str | None = None


def build_live_phase_handlers(
    repo_root: str | Path,
    *,
    config_path: str | Path | None = None,
    model: str = DEFAULT_MODEL,
    aris_bin: str = "aris",
    runner: Callable[..., Any] = subprocess.run,
    tavily_api_key: str | None = None,
    github_token: str | None = None,
    tavily_transport: Transport = default_transport,
    github_transport: Transport = default_transport,
    direct_transport: Transport = default_transport,
    clock: Callable[[], str] = utc_now_iso,
) -> Mapping[Phase, Callable[[str, ProductState], PhaseOutcome]]:
    pipeline = LivePipeline(
        repo_root=Path(repo_root),
        config_path=Path(config_path) if config_path is not None else None,
        model=model,
        aris_bin=aris_bin,
        runner=runner,
        tavily_api_key=tavily_api_key,
        github_token=github_token,
        tavily_transport=tavily_transport,
        github_transport=github_transport,
        direct_transport=direct_transport,
        clock=clock,
    )
    return {
        Phase.PLAN_QUERIES: pipeline.plan_queries,
        Phase.FETCH: pipeline.fetch,
        Phase.DIGEST: pipeline.digest,
        Phase.PROFILE: pipeline.profile,
        Phase.VENDOR_SKEPTIC: pipeline.vendor_skeptic,
        Phase.ARBITER: pipeline.arbiter,
        Phase.APPLY: pipeline.apply,
        Phase.VERIFY: pipeline.verify,
        Phase.COMPILE: pipeline.compile,
    }


class LivePipeline:
    def __init__(
        self,
        *,
        repo_root: Path,
        config_path: Path | None,
        model: str,
        aris_bin: str,
        runner: Callable[..., Any],
        tavily_api_key: str | None,
        github_token: str | None,
        tavily_transport: Transport,
        github_transport: Transport,
        direct_transport: Transport,
        clock: Callable[[], str],
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.config_path = (config_path or (self.repo_root / DEFAULT_SOURCES_PATH)).resolve()
        self.model = model
        self.aris_bin = aris_bin
        self.runner = runner
        self.tavily_api_key = tavily_api_key
        self.github_token = github_token
        self.tavily_transport = tavily_transport
        self.github_transport = github_transport
        self.direct_transport = direct_transport
        self.clock = clock
        self.products = _load_sources_manifest(self.config_path)

    def plan_queries(self, slug: str, _state: ProductState) -> PhaseOutcome:
        product = self._product(slug)
        workspace = self._reset_workspace(slug, "inbox-plan")
        atomic_write_json(workspace / "seed.json", _seed_payload(product))
        return self._run_model_phase(
            slug=slug,
            workspace=workspace,
            prompt=f"/geo-plan-queries --slug {slug}",
            expected_output=workspace / "queries.json",
            required_tools=("read_file", "write_file"),
            persist_to=self._raw_dir(slug) / "queries.json",
            validator=_validate_queries_payload,
        )

    def fetch(self, slug: str, _state: ProductState) -> PhaseOutcome:
        product = self._product(slug)
        raw_dir = self._raw_dir(slug)
        raw_dir.mkdir(parents=True, exist_ok=True)

        try:
            records: list[dict[str, Any]] = []
            seen_urls: set[tuple[str, str]] = set()
            sequence = 1

            queries = self._load_queries(raw_dir / "queries.json")
            if self.tavily_api_key and queries:
                tavily_client = TavilyClient(
                    self.repo_root / DEFAULT_TAVILY_CACHE_DIR,
                    api_key=self.tavily_api_key,
                    transport=self.tavily_transport,
                    clock=self.clock,
                )
                for index, query_spec in enumerate(queries, start=1):
                    snapshot_path = raw_dir / f"tavily-query-{index}.json"
                    payload = tavily_client.search(
                        query_spec["query"],
                        snapshot_path=snapshot_path,
                    )
                    for result in payload.get("results", []):
                        if not isinstance(result, dict):
                            continue
                        url = result.get("url")
                        if not isinstance(url, str) or not url.strip():
                            continue
                        dedupe_key = (url.strip(), query_spec["kind"])
                        if dedupe_key in seen_urls:
                            continue
                        text = _search_result_text(result)
                        if not text.strip():
                            continue
                        record = self._write_evidence_record(
                            raw_dir=raw_dir,
                            evidence_id=f"e{sequence}",
                            url=url.strip(),
                            kind=query_spec["kind"],
                            text=text,
                            fetched_at=self._fetched_on(),
                        )
                        sequence += 1
                        seen_urls.add(dedupe_key)
                        records.append(record)

            for entry in product.urls:
                dedupe_key = (entry.url, entry.kind)
                if dedupe_key in seen_urls:
                    continue
                response = self.direct_transport(
                    HttpRequest(
                        method="GET",
                        url=entry.url,
                        headers={"Accept": "text/plain, text/html, application/json;q=0.9"},
                    )
                )
                if not 200 <= response.status < 300:
                    raise RuntimeError(f"direct URL request failed with HTTP {response.status}: {entry.url}")
                record = self._write_evidence_record(
                    raw_dir=raw_dir,
                    evidence_id=f"e{sequence}",
                    url=entry.url,
                    kind=entry.kind,
                    text=response.body.decode("utf-8", errors="replace"),
                    fetched_at=self._fetched_on(),
                )
                sequence += 1
                seen_urls.add(dedupe_key)
                records.append(record)

            repo_health = None
            if product.repo:
                github_client = GitHubHealthClient(
                    self.repo_root / DEFAULT_GITHUB_CACHE_DIR,
                    token=self.github_token,
                    transport=self.github_transport,
                    clock=self.clock,
                )
                repo_health = github_client.repository_health(*product.repo.split("/", 1))
                atomic_write_json(raw_dir / "github_health.json", repo_health)
                record = self._write_evidence_record(
                    raw_dir=raw_dir,
                    evidence_id=f"e{sequence}",
                    url=f"https://github.com/{product.repo}",
                    kind="repo",
                    text=_repo_health_text(repo_health),
                    fetched_at=self._fetched_on(),
                )
                sequence += 1
                records.append(record)

            if not records and not self.tavily_api_key:
                return PhaseOutcome(
                    success=False,
                    error="no direct urls configured and Tavily API key is absent",
                )
            if not records:
                return PhaseOutcome(success=False, error="fetch produced no evidence records")

            atomic_write_json(raw_dir / "evidence_inputs.json", records)
            if repo_health is None and (raw_dir / "github_health.json").exists():
                (raw_dir / "github_health.json").unlink()
            return PhaseOutcome(success=True, tokens=0)
        except Exception as exc:
            return PhaseOutcome(success=False, error=str(exc))

    def digest(self, slug: str, _state: ProductState) -> PhaseOutcome:
        workspace = self._reset_workspace(slug, "inbox-digest")
        raw_dir = self._raw_dir(slug)
        self._copy_required(raw_dir / "evidence_inputs.json", workspace / "evidence_inputs.json")
        for text_path in sorted(raw_dir.glob("e*.txt")):
            self._copy_required(text_path, workspace / text_path.name)
        return self._run_model_phase(
            slug=slug,
            workspace=workspace,
            prompt=f"/geo-digest --slug {slug}",
            expected_output=workspace / "evidence.md",
            required_tools=("read_file", "write_file"),
            persist_to=raw_dir / "evidence.md",
        )

    def profile(self, slug: str, _state: ProductState) -> PhaseOutcome:
        workspace = self._reset_workspace(slug, "inbox-profile")
        raw_dir = self._raw_dir(slug)
        product = self._product(slug)
        self._copy_required(raw_dir / "evidence.md", workspace / "evidence.md")
        self._copy_required(raw_dir / "evidence_inputs.json", workspace / "evidence_inputs.json")
        atomic_write_json(workspace / "seed.json", _seed_payload(product))
        outcome = self._run_model_phase(
            slug=slug,
            workspace=workspace,
            prompt=f"/geo-profile --slug {slug}",
            expected_output=workspace / f"{slug}.json",
            required_tools=("read_file", "write_file"),
            persist_to=self.repo_root / "wiki" / "products" / f"{slug}.json",
            validator=_validate_profile_payload,
        )
        if not outcome.success:
            return outcome
        try:
            self._normalize_profile(slug)
        except Exception as exc:
            return PhaseOutcome(success=False, error=str(exc))
        return outcome

    def vendor_skeptic(self, slug: str, _state: ProductState) -> PhaseOutcome:
        total_tokens = 0
        for persona in ("vendor", "skeptic"):
            inbox = stage_persona_inbox(self.repo_root, slug, persona)
            prompt = f"/geo-review --persona {persona} --slug {slug}"
            expected = inbox / f"{persona}.json"
            outcome = self._run_model_phase(
                slug=slug,
                workspace=inbox,
                prompt=prompt,
                expected_output=expected,
                required_tools=("read_file", "write_file"),
                persist_to=self.repo_root / "wiki" / "review" / slug / f"{persona}.json",
            )
            if not outcome.success:
                return outcome
            total_tokens += outcome.tokens
        return PhaseOutcome(success=True, tokens=total_tokens)

    def arbiter(self, slug: str, _state: ProductState) -> PhaseOutcome:
        inbox = stage_persona_inbox(self.repo_root, slug, "arbiter")
        return self._run_model_phase(
            slug=slug,
            workspace=inbox,
            prompt=f"/geo-review --persona arbiter --slug {slug}",
            expected_output=inbox / "patch.json",
            required_tools=("read_file", "write_file"),
            persist_to=self.repo_root / "wiki" / "review" / slug / "patch.json",
            validator=_validate_patch_payload,
        )

    def apply(self, slug: str, _state: ProductState) -> PhaseOutcome:
        try:
            profile_path = self.repo_root / "wiki" / "products" / f"{slug}.json"
            patch_path = self.repo_root / "wiki" / "review" / slug / "patch.json"
            profile = _read_json_object(profile_path, "profile")
            payload = _read_json_object(patch_path, "patch")
            _validate_patch_payload(payload)
            operations = payload["patch"]
            seen_fields: set[str] = set()
            for operation in operations:
                field = operation["field"]
                if field in seen_fields:
                    raise ValueError(f"duplicate patch field: {field}")
                seen_fields.add(field)
                if not _is_allowed_patch_field(field):
                    raise ValueError(f"patch field is not allowed: {field}")
                _apply_set_operation(profile, field, operation["value"])
            profile["unresolved"] = payload["unresolved"]
            github_health_path = self._raw_dir(slug) / "github_health.json"
            if github_health_path.is_file():
                profile["oss_health"] = _read_json_object(github_health_path, "GitHub health")
            atomic_write_json(profile_path, profile)
            return PhaseOutcome(success=True, tokens=0)
        except Exception as exc:
            return PhaseOutcome(success=False, error=str(exc))

    def verify(self, slug: str, _state: ProductState) -> PhaseOutcome:
        from tools import score as score_tool
        from tools import verify_evidence as verify_tool

        profile_path = self.repo_root / "wiki" / "products" / f"{slug}.json"
        try:
            profile = _read_json_object(profile_path, "profile")
            updated = score_tool._recompute_profile(profile)
            if updated != profile:
                atomic_write_json(profile_path, updated)
            errors = verify_tool._validate_profile_path(profile_path, self.repo_root, strict=True)
            if errors:
                return PhaseOutcome(success=False, error="; ".join(errors), retry_review=True)
            return PhaseOutcome(success=True, tokens=0)
        except Exception as exc:
            return PhaseOutcome(success=False, error=str(exc), retry_review=True)

    def compile(self, _slug: str, _state: ProductState) -> PhaseOutcome:
        try:
            current_readme, rendered = compile_readme(self.repo_root)
            if current_readme != rendered:
                (self.repo_root / "README.md").write_text(rendered, encoding="utf-8")
            return PhaseOutcome(success=True, tokens=0)
        except Exception as exc:
            return PhaseOutcome(success=False, error=str(exc))

    def _run_model_phase(
        self,
        *,
        slug: str,
        workspace: Path,
        prompt: str,
        expected_output: Path,
        required_tools: Sequence[str],
        persist_to: Path,
        validator: Callable[[Any], None] | None = None,
    ) -> PhaseOutcome:
        try:
            result = run_aris_phase(
                prompt=prompt,
                model=self.model,
                cwd=workspace,
                runner=self.runner,
                aris_bin=self.aris_bin,
                required_tools=required_tools,
            )
            if not expected_output.is_file():
                raise FileNotFoundError(f"{prompt}: missing output file {expected_output.name}")
            if validator is not None:
                validator(json.loads(expected_output.read_text(encoding="utf-8")))
            self._copy_required(expected_output, persist_to)
            return PhaseOutcome(success=True, tokens=_model_tokens(result))
        except Exception as exc:
            return PhaseOutcome(success=False, error=f"{prompt}: {exc}")

    def _normalize_profile(self, slug: str) -> None:
        product = self._product(slug)
        profile_path = self.repo_root / "wiki" / "products" / f"{slug}.json"
        profile = _read_json_object(profile_path, "profile")
        evidence_inputs = json.loads((self._raw_dir(slug) / "evidence_inputs.json").read_text(encoding="utf-8"))
        if not isinstance(evidence_inputs, list):
            raise ValueError("evidence_inputs.json must contain a list")
        profile["schema_version"] = "v1"
        profile["slug"] = slug
        profile["market"] = product.market
        profile["category"] = list(product.category)
        profile["openness"] = product.openness
        profile["evidence"] = evidence_inputs
        profile.setdefault("unknowns", [])
        profile.setdefault("case_studies", [])
        atomic_write_json(profile_path, profile)

    def _reset_workspace(self, slug: str, name: str) -> Path:
        workspace = self.repo_root / "wiki" / "review" / slug / name
        if workspace.exists():
            shutil.rmtree(workspace)
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def _copy_required(self, source: Path, destination: Path) -> None:
        if not source.is_file():
            raise FileNotFoundError(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    def _product(self, slug: str) -> ProductSource:
        try:
            return self.products[slug]
        except KeyError as exc:
            raise KeyError(f"unknown slug in sources manifest: {slug}") from exc

    def _raw_dir(self, slug: str) -> Path:
        return self.repo_root / "wiki" / "raw" / slug

    def _load_queries(self, path: Path) -> list[dict[str, str]]:
        if not path.is_file():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return _normalize_queries(payload)

    def _write_evidence_record(
        self,
        *,
        raw_dir: Path,
        evidence_id: str,
        url: str,
        kind: str,
        text: str,
        fetched_at: str,
    ) -> dict[str, Any]:
        excerpt_path = raw_dir / f"{evidence_id}.txt"
        excerpt_path.write_text(text, encoding="utf-8")
        from .evidence import sha256_file

        return {
            "id": evidence_id,
            "url": url,
            "kind": kind,
            "fetched_at": fetched_at,
            "sha256": sha256_file(excerpt_path),
            "excerpt_path": f"wiki/raw/{raw_dir.name}/{excerpt_path.name}",
            "paid_placement_suspected": False,
        }

    def _fetched_on(self) -> str:
        return self.clock().split("T", 1)[0]


def _load_sources_manifest(path: Path) -> dict[str, ProductSource]:
    payload = _read_json_object(path, "sources manifest")
    products = payload.get("products")
    if not isinstance(products, list):
        raise ValueError("sources manifest: products must be a list")

    result: dict[str, ProductSource] = {}
    for entry in products:
        if not isinstance(entry, dict):
            raise ValueError("sources manifest: product entries must be objects")
        slug = entry.get("slug")
        name = entry.get("name")
        market = entry.get("market")
        openness = entry.get("openness")
        category = entry.get("category")
        urls = entry.get("urls")
        repo = entry.get("repo")
        if not all(isinstance(value, str) and value.strip() for value in (slug, name, market, openness)):
            raise ValueError("sources manifest: slug, name, market, and openness are required strings")
        if not isinstance(category, list) or not category or not all(isinstance(item, str) and item.strip() for item in category):
            raise ValueError(f"sources manifest: category must be a non-empty string list for {slug}")
        if not isinstance(urls, list):
            raise ValueError(f"sources manifest: urls must be a list for {slug}")
        manifest_urls = []
        for item in urls:
            if not isinstance(item, dict):
                raise ValueError(f"sources manifest: url entries must be objects for {slug}")
            url = item.get("url")
            kind = item.get("kind")
            if not (isinstance(url, str) and url.strip() and isinstance(kind, str) and kind.strip()):
                raise ValueError(f"sources manifest: each url entry needs url and kind for {slug}")
            manifest_urls.append(ManifestUrl(url=url.strip(), kind=kind.strip()))
        if repo is not None:
            if not isinstance(repo, str) or repo.count("/") != 1:
                raise ValueError(f"sources manifest: repo must be owner/name for {slug}")
            repo = repo.strip().lower()
        if slug in result:
            raise ValueError(f"sources manifest: duplicate slug {slug}")
        result[slug] = ProductSource(
            slug=slug.strip(),
            name=name.strip(),
            market=market.strip(),
            category=tuple(item.strip() for item in category),
            openness=openness.strip(),
            urls=tuple(manifest_urls),
            repo=repo,
        )
    return result


def _seed_payload(product: ProductSource) -> dict[str, Any]:
    payload = {
        "slug": product.slug,
        "name": product.name,
        "market": product.market,
        "category": list(product.category),
        "openness": product.openness,
        "urls": [{"url": item.url, "kind": item.kind} for item in product.urls],
    }
    if product.repo is not None:
        payload["repo"] = product.repo
    return payload


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} at {path} is invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} at {path} must be a JSON object")
    return payload


def _validate_queries_payload(payload: Any) -> None:
    _normalize_queries(payload)


def _normalize_queries(payload: Any) -> list[dict[str, str]]:
    if not isinstance(payload, list):
        raise ValueError("queries.json must contain a list")
    queries: list[dict[str, str]] = []
    for item in payload:
        if isinstance(item, str) and item.strip():
            queries.append({"query": item.strip(), "kind": "community"})
            continue
        if isinstance(item, dict):
            query = item.get("query")
            kind = item.get("kind", "community")
            if isinstance(query, str) and query.strip() and isinstance(kind, str) and kind.strip():
                queries.append({"query": query.strip(), "kind": kind.strip()})
                continue
        raise ValueError("queries.json entries must be strings or objects with query/kind")
    return queries


def _validate_profile_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValueError("profile output must be a JSON object")


def _validate_patch_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValueError("patch.json must be a JSON object")
    patch = payload.get("patch")
    unresolved = payload.get("unresolved")
    if not isinstance(patch, list):
        raise ValueError("patch.json: patch must be a list")
    if not isinstance(unresolved, list):
        raise ValueError("patch.json: unresolved must be a list")
    for operation in patch:
        if not isinstance(operation, dict):
            raise ValueError("patch.json: patch entries must be objects")
        if operation.get("op") != "set":
            raise ValueError("patch.json: only set operations are supported")
        field = operation.get("field")
        if not isinstance(field, str) or not field.strip():
            raise ValueError("patch.json: each patch entry needs a non-empty field")
        if "value" not in operation:
            raise ValueError("patch.json: each patch entry needs a value")


def _is_allowed_patch_field(field: str) -> bool:
    root = field.split(".", 1)[0].split("[", 1)[0]
    return root in PATCH_ROOT_ALLOWLIST


def _apply_set_operation(profile: dict[str, Any], field: str, value: Any) -> None:
    parts = _path_parts(field)
    current: Any = profile
    for index, part in enumerate(parts[:-1]):
        if isinstance(part, int):
            if not isinstance(current, list):
                raise ValueError(f"patch field path expects a list at {field}")
            if part < 0 or part >= len(current):
                raise ValueError(f"patch field index out of range at {field}")
            current = current[part]
            continue
        if not isinstance(current, dict):
            raise ValueError(f"patch field path expects an object at {field}")
        if part not in current:
            current[part] = {} if not isinstance(parts[index + 1], int) else []
        current = current[part]

    final = parts[-1]
    if isinstance(final, int):
        if not isinstance(current, list):
            raise ValueError(f"patch field path expects a list at {field}")
        if final < 0 or final >= len(current):
            raise ValueError(f"patch field index out of range at {field}")
        current[final] = value
        return
    if not isinstance(current, dict):
        raise ValueError(f"patch field path expects an object at {field}")
    current[final] = value


def _path_parts(field: str) -> list[str | int]:
    parts: list[str | int] = []
    for chunk in field.split("."):
        segment = chunk
        while "[" in segment:
            prefix, remainder = segment.split("[", 1)
            if prefix:
                parts.append(prefix)
            index_text, segment = remainder.split("]", 1)
            parts.append(int(index_text))
        if segment:
            parts.append(segment)
    if not parts:
        raise ValueError("patch field must not be empty")
    return parts


def _search_result_text(result: Mapping[str, Any]) -> str:
    for key in ("raw_content", "content", "summary", "title"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return json.dumps(result, ensure_ascii=False, sort_keys=True)


def _repo_health_text(payload: Mapping[str, Any]) -> str:
    return (
        f"Repository: {payload.get('full_name')}\n"
        f"Stars: {payload.get('stars')}\n"
        f"Contributors(12mo): {payload.get('contributors_12mo')}\n"
        f"Commits(90d): {payload.get('commits_90d')}\n"
        f"Releases: {payload.get('releases')}\n"
        f"Last release: {payload.get('last_release')}\n"
        f"License: {payload.get('license_spdx')}\n"
    )


def _model_tokens(result: ArisResult) -> int:
    return int(result.usage.get("input_tokens", 0)) + int(result.usage.get("output_tokens", 0))
