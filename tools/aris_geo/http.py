from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib import error, request


@dataclass(frozen=True)
class HttpRequest:
    method: str
    url: str
    headers: Mapping[str, str]
    body: bytes | None = None


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes


Transport = Callable[[HttpRequest], HttpResponse]


def default_transport(http_request: HttpRequest) -> HttpResponse:
    req = request.Request(
        http_request.url,
        data=http_request.body,
        headers=dict(http_request.headers),
        method=http_request.method.upper(),
    )
    try:
        with request.urlopen(req) as response:
            return HttpResponse(
                status=getattr(response, "status", response.getcode()),
                headers=dict(response.headers.items()),
                body=response.read(),
            )
    except error.HTTPError as exc:
        return HttpResponse(
            status=exc.code,
            headers=dict(exc.headers.items()),
            body=exc.read(),
        )
    except error.URLError as exc:
        raise RuntimeError(f"network request failed: {exc.reason}") from exc


def canonical_request_sha256(http_request: HttpRequest) -> str:
    canonical = {
        "method": http_request.method.upper(),
        "url": http_request.url,
        "headers": _canonical_headers(http_request.headers),
        "body": _canonical_body(http_request.body, http_request.headers),
    }
    return hashlib.sha256(_compact_json_bytes(canonical)).hexdigest()


def cache_path(cache_dir: str | Path, http_request: HttpRequest) -> Path:
    return Path(cache_dir) / f"{canonical_request_sha256(http_request)}.json"


def load_cached_json(path: str | Path) -> Any | None:
    cache_file = Path(path)
    if not cache_file.is_file():
        return None
    payload = json.loads(cache_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"cached snapshot at {cache_file} must be an object")
    fetched_at = payload.get("fetched_at")
    sha256 = payload.get("sha256")
    content = payload.get("content")
    if not isinstance(fetched_at, str) or not fetched_at:
        raise ValueError(f"cached snapshot at {cache_file} is missing fetched_at")
    if not isinstance(sha256, str) or len(sha256) != 64:
        raise ValueError(f"cached snapshot at {cache_file} is missing sha256")
    if sha256 != content_sha256(content):
        raise ValueError(f"cached snapshot at {cache_file} has mismatched sha256")
    return content


def atomic_write_snapshot(path: str | Path, content: Any, fetched_at: str) -> None:
    payload = {
        "fetched_at": fetched_at,
        "sha256": content_sha256(content),
        "content": content,
    }
    atomic_write_json(path, payload)


def atomic_write_json(path: str | Path, payload: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    fd, temp_path = tempfile.mkstemp(dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise


def content_sha256(content: Any) -> str:
    return hashlib.sha256(_stable_json_bytes(content)).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_json_response(response: HttpResponse, service_name: str) -> Any:
    if not 200 <= response.status < 300:
        raise RuntimeError(f"{service_name} request failed with HTTP {response.status}")
    try:
        return json.loads(response.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{service_name} response must be valid JSON") from exc


def _canonical_headers(headers: Mapping[str, str]) -> dict[str, str]:
    canonical: dict[str, str] = {}
    for key, value in headers.items():
        lowered = key.strip().lower()
        if lowered in {"authorization", "proxy-authorization"}:
            continue
        canonical[lowered] = value.strip()
    return canonical


def _canonical_body(body: bytes | None, headers: Mapping[str, str]) -> Any:
    if body is None:
        return None
    content_type = ""
    for key, value in headers.items():
        if key.strip().lower() == "content-type":
            content_type = value
            break
    if "application/json" in content_type.lower():
        return json.loads(body.decode("utf-8"))
    return body.decode("utf-8")


def _compact_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _stable_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
