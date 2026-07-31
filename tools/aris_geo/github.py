from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode

from .http import (
    HttpRequest,
    Transport,
    atomic_write_snapshot,
    cache_path,
    content_sha256,
    default_transport,
    load_cached_json,
    parse_json_response,
    utc_now_iso,
)

AGGREGATE_SCHEMA_VERSION = "github-health-v1"


class GitHubHealthClient:
    def __init__(
        self,
        cache_dir: str | Path,
        *,
        token: str | None = None,
        transport: Transport = default_transport,
        clock: Callable[[], str] = utc_now_iso,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.token = token
        self.transport = transport
        self.clock = clock

    def repository_health(self, owner: str, repo: str) -> dict[str, Any]:
        return self.collect(owner, repo)

    def collect(self, owner: str, repo: str) -> dict[str, Any]:
        owner, repo = self._normalize_repository(owner, repo)
        aggregate_path = self.aggregate_cache_path(owner, repo)
        force_live_fetch = False
        try:
            cached = load_cached_json(aggregate_path)
        except ValueError:
            cached = None
            if not self._has_live_token():
                raise ValueError("GitHub token required for live request")
            force_live_fetch = True
        else:
            if cached is not None:
                self._validate_aggregate_health(cached)
                return cached

        if not self._has_live_token():
            raise ValueError("GitHub token required for live request")

        repo_payload = self._fetch_json(
            self._request("GET", f"/repos/{owner}/{repo}"),
            validator=lambda payload: self._require_repo_field(payload, "full_name"),
            force_live_fetch=force_live_fetch,
        )

        contributors = self._fetch_json(
            self._request("GET", f"/repos/{owner}/{repo}/contributors", {"per_page": "100"}),
            validator=self._require_list("contributors"),
            force_live_fetch=force_live_fetch,
        )
        commits = self._fetch_json(
            self._request(
                "GET",
                f"/repos/{owner}/{repo}/commits",
                {
                    "since": self._commits_since_iso(),
                    "per_page": "100",
                },
            ),
            validator=self._require_list("commits"),
            force_live_fetch=force_live_fetch,
        )
        releases = self._fetch_json(
            self._request("GET", f"/repos/{owner}/{repo}/releases", {"per_page": "100"}),
            validator=self._require_list("releases"),
            force_live_fetch=force_live_fetch,
        )

        license_payload = repo_payload.get("license")
        license_spdx = None
        if isinstance(license_payload, dict):
            license_spdx = license_payload.get("spdx_id")
        if license_spdx in {"NOASSERTION", ""}:
            license_spdx = None

        result = {
            "full_name": repo_payload["full_name"],
            "html_url": repo_payload.get("html_url"),
            "description": repo_payload.get("description"),
            "topics": repo_payload.get("topics") if isinstance(repo_payload.get("topics"), list) else [],
            "archived": bool(repo_payload.get("archived")),
            "fork": bool(repo_payload.get("fork")),
            "stars": int(repo_payload.get("stargazers_count") or 0),
            "watchers": int(repo_payload.get("watchers_count") or 0),
            "forks": int(repo_payload.get("forks_count") or 0),
            "open_issues": int(repo_payload.get("open_issues_count") or 0),
            "subscribers": int(repo_payload.get("subscribers_count") or 0),
            "network_count": int(repo_payload.get("network_count") or 0),
            "size_kb": int(repo_payload.get("size") or 0),
            "default_branch": repo_payload.get("default_branch"),
            "created_at": repo_payload.get("created_at"),
            "updated_at": repo_payload.get("updated_at"),
            "pushed_at": repo_payload.get("pushed_at"),
            "license_spdx": license_spdx,
            "license_absent": license_spdx is None,
            "contributors_12mo": len(contributors),
            "commits_90d": len(commits),
            "releases": len(releases),
            "last_release": releases[0].get("published_at") if releases else None,
        }
        self._validate_aggregate_health(result)
        atomic_write_snapshot(aggregate_path, result, self.clock())
        return result

    def aggregate_cache_path(self, owner: str, repo: str) -> Path:
        owner, repo = self._normalize_repository(owner, repo)
        key = content_sha256(
            {
                "schema_version": AGGREGATE_SCHEMA_VERSION,
                "owner": owner,
                "repo": repo,
            }
        )
        return self.cache_dir / "aggregate" / f"{key}.json"

    def _fetch_json(
        self,
        http_request: HttpRequest,
        *,
        validator: Callable[[Any], None] | None = None,
        force_live_fetch: bool = False,
    ) -> Any:
        if not force_live_fetch:
            cached = load_cached_json(cache_path(self.cache_dir, http_request))
            if cached is not None:
                if validator is not None:
                    validator(cached)
                return cached
        payload = parse_json_response(self.transport(http_request), "GitHub")
        if validator is not None:
            validator(payload)

        atomic_write_snapshot(cache_path(self.cache_dir, http_request), payload, self.clock())
        return payload

    def _request(self, method: str, path: str, query: dict[str, str] | None = None) -> HttpRequest:
        url = f"https://api.github.com{path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return HttpRequest(method=method, url=url, headers=headers)

    def _has_live_token(self) -> bool:
        return isinstance(self.token, str) and bool(self.token.strip())

    @staticmethod
    def _require_repo_field(payload: Any, field_name: str) -> None:
        if not isinstance(payload, dict) or field_name not in payload:
            raise ValueError(f"GitHub repository response missing required field: {field_name}")

    @staticmethod
    def _require_list(name: str) -> Callable[[Any], None]:
        def validate(payload: Any) -> None:
            if not isinstance(payload, list):
                raise ValueError(f"GitHub {name} response must be a list")

        return validate

    @staticmethod
    def _normalize_repository(owner: str, repo: str) -> tuple[str, str]:
        return owner.strip().lower(), repo.strip().lower()

    @staticmethod
    def _validate_aggregate_health(payload: Any) -> None:
        required_fields = (
            "full_name",
            "html_url",
            "archived",
            "fork",
            "stars",
            "watchers",
            "forks",
            "open_issues",
            "subscribers",
            "network_count",
            "size_kb",
            "default_branch",
            "created_at",
            "updated_at",
            "pushed_at",
            "license_absent",
            "contributors_12mo",
            "commits_90d",
            "releases",
            "last_release",
        )
        if not isinstance(payload, dict):
            raise ValueError("GitHub aggregate cache content must be an object")
        for field_name in required_fields:
            if field_name not in payload:
                raise ValueError(f"GitHub aggregate cache missing required field: {field_name}")

    @staticmethod
    def _commits_since_iso() -> str:
        return (
            datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=90)
        ).isoformat().replace("+00:00", "Z")
