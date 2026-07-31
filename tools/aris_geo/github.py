from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode

from .http import (
    HttpRequest,
    Transport,
    cache_path,
    default_transport,
    load_cached_json,
    parse_json_response,
    utc_now_iso,
)


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
        repo_payload = self._fetch_json(
            self._request("GET", f"/repos/{owner}/{repo}"),
            validator=lambda payload: self._require_repo_field(payload, "full_name"),
        )

        contributors = self._fetch_json(
            self._request("GET", f"/repos/{owner}/{repo}/contributors", {"per_page": "100"}),
            validator=self._require_list("contributors"),
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
        )
        releases = self._fetch_json(
            self._request("GET", f"/repos/{owner}/{repo}/releases", {"per_page": "100"}),
            validator=self._require_list("releases"),
        )

        license_payload = repo_payload.get("license")
        license_spdx = None
        if isinstance(license_payload, dict):
            license_spdx = license_payload.get("spdx_id")
        if license_spdx in {"NOASSERTION", ""}:
            license_spdx = None

        return {
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

    def _fetch_json(
        self,
        http_request: HttpRequest,
        *,
        validator: Callable[[Any], None] | None = None,
    ) -> Any:
        cached = load_cached_json(cache_path(self.cache_dir, http_request))
        if cached is not None:
            if validator is not None:
                validator(cached)
            return cached
        payload = parse_json_response(self.transport(http_request), "GitHub")
        if validator is not None:
            validator(payload)
        from .http import atomic_write_snapshot  # local import to keep the public surface small

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
    def _commits_since_iso() -> str:
        return (
            datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=90)
        ).isoformat().replace("+00:00", "Z")
