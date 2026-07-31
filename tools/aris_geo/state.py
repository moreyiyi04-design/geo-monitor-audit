from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class Phase(str, Enum):
    PLAN_QUERIES = "plan_queries"
    FETCH = "fetch"
    DIGEST = "digest"
    PROFILE = "profile"
    VENDOR_SKEPTIC = "vendor_skeptic"
    ARBITER = "arbiter"
    APPLY = "apply"
    VERIFY = "verify"
    COMPILE = "compile"
    PASS = "pass"


@dataclass(frozen=True)
class ProductState:
    slug: str
    phase: Phase = Phase.PLAN_QUERIES
    round: int = 0
    cost_so_far: int = 0
    last_error: str | None = None
    evidence_fingerprint: str | None = None


def load_state(repo_root: str | Path, slug: str) -> ProductState:
    path = _state_path(repo_root, slug)
    if not path.exists():
        return ProductState(slug=slug)

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"invalid state payload for {slug}")

    phase = Phase(payload.get("phase", Phase.PLAN_QUERIES.value))
    round_value = payload.get("round", 0)
    cost_value = payload.get("cost_so_far", 0)
    if isinstance(round_value, bool) or not isinstance(round_value, int) or round_value < 0:
        raise ValueError(f"invalid round for {slug}")
    if isinstance(cost_value, bool) or not isinstance(cost_value, int) or cost_value < 0:
        raise ValueError(f"invalid cost_so_far for {slug}")

    last_error = payload.get("last_error")
    if last_error is not None and not isinstance(last_error, str):
        raise ValueError(f"invalid last_error for {slug}")

    fingerprint = payload.get("evidence_fingerprint")
    if fingerprint is not None and not isinstance(fingerprint, str):
        raise ValueError(f"invalid evidence_fingerprint for {slug}")

    return ProductState(
        slug=str(payload.get("slug") or slug),
        phase=phase,
        round=round_value,
        cost_so_far=cost_value,
        last_error=last_error,
        evidence_fingerprint=fingerprint,
    )


def save_state(repo_root: str | Path, state: ProductState) -> Path:
    path = _state_path(repo_root, state.slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = asdict(state)
    payload["phase"] = state.phase.value
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(serialized)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)
    return path


def evidence_fingerprint(repo_root: str | Path, slug: str) -> str:
    raw_dir = _raw_dir(repo_root, slug)
    if not raw_dir.is_dir():
        raise FileNotFoundError(raw_dir)

    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in raw_dir.rglob("*") if candidate.is_file()):
        if path.is_symlink():
            raise ValueError(f"refuses symlinked evidence file: {path}")
        relative_name = path.relative_to(raw_dir).as_posix().encode("utf-8")
        digest.update(len(relative_name).to_bytes(4, "big"))
        digest.update(relative_name)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _state_path(repo_root: str | Path, slug: str) -> Path:
    _validate_slug(slug)
    return Path(repo_root) / "wiki" / "state" / f"{slug}.json"


def _raw_dir(repo_root: str | Path, slug: str) -> Path:
    _validate_slug(slug)
    return Path(repo_root) / "wiki" / "raw" / slug


def _validate_slug(slug: Any) -> None:
    if not isinstance(slug, str) or not slug:
        raise ValueError("slug must be a non-empty string")
    slug_path = Path(slug)
    if slug in {".", ".."} or slug_path.name != slug or len(slug_path.parts) != 1:
        raise ValueError("slug escapes repository root")
