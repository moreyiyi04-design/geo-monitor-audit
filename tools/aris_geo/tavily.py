from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .http import (
    HttpRequest,
    Transport,
    atomic_write_snapshot,
    cache_path,
    default_transport,
    load_cached_json,
    parse_json_response,
    utc_now_iso,
)


class TavilyClient:
    def __init__(
        self,
        cache_dir: str | Path,
        *,
        api_key: str | None = None,
        transport: Transport = default_transport,
        clock: Callable[[], str] = utc_now_iso,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.api_key = api_key
        self.transport = transport
        self.clock = clock

    def build_request(
        self,
        query: str,
        *,
        max_results: int = 5,
        topic: str = "general",
        search_depth: str = "advanced",
        include_raw_content: bool = True,
    ) -> HttpRequest:
        payload = {
            "query": query,
            "topic": topic,
            "search_depth": search_depth,
            "max_results": max_results,
            "include_raw_content": include_raw_content,
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return HttpRequest(
            method="POST",
            url="https://api.tavily.com/search",
            headers=headers,
            body=json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"),
        )

    def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        topic: str = "general",
        search_depth: str = "advanced",
        include_raw_content: bool = True,
        snapshot_path: str | Path | None = None,
    ) -> dict[str, Any]:
        http_request = self.build_request(
            query,
            max_results=max_results,
            topic=topic,
            search_depth=search_depth,
            include_raw_content=include_raw_content,
        )
        cached = load_cached_json(cache_path(self.cache_dir, http_request))
        if cached is not None:
            self._validate_search_payload(cached)
            return cached
        if not self.api_key:
            raise ValueError("Tavily API key required for live request")

        payload = parse_json_response(self.transport(http_request), "Tavily")
        self._validate_search_payload(payload)
        fetched_at = self.clock()
        atomic_write_snapshot(cache_path(self.cache_dir, http_request), payload, fetched_at)
        if snapshot_path is not None:
            atomic_write_snapshot(snapshot_path, payload, fetched_at)
        return payload

    @staticmethod
    def _validate_search_payload(payload: Any) -> None:
        if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
            raise ValueError("Tavily response must contain a results list")
