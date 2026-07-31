from __future__ import annotations

import shutil
from pathlib import Path


PERSONA_ALLOWLIST: dict[str, tuple[str, ...]] = {
    "vendor": ("evidence", "profile"),
    "skeptic": ("evidence", "profile"),
    "arbiter": ("evidence", "vendor", "skeptic"),
}


def stage_persona_inbox(repo_root: str | Path, slug: str, persona: str) -> Path:
    repo_root = Path(repo_root).resolve()
    if persona not in PERSONA_ALLOWLIST:
        raise ValueError(f"unknown persona: {persona}")
    _validate_slug(slug)

    review_dir = _resolve_under_repo(repo_root, "slug escapes repository root", "wiki", "review", slug)
    inbox = review_dir / f"inbox-{persona}"
    if inbox.exists():
        if inbox.is_symlink():
            raise ValueError(f"refuses symlinked inbox: {inbox}")
        shutil.rmtree(inbox)
    inbox.mkdir(parents=True, exist_ok=True)

    source_map = {
        "evidence": _source_file(repo_root, "wiki", "raw", slug, "evidence.md"),
        "profile": _source_file(repo_root, "wiki", "products", f"{slug}.json"),
        "vendor": _source_file(repo_root, "wiki", "review", slug, "vendor.json"),
        "skeptic": _source_file(repo_root, "wiki", "review", slug, "skeptic.json"),
    }

    for key in PERSONA_ALLOWLIST[persona]:
        source = source_map[key]
        shutil.copyfile(source, inbox / source.name)

    return inbox


def _source_file(repo_root: Path, *relative_parts: str) -> Path:
    relative_path = Path(*relative_parts)
    source = repo_root / relative_path
    if source.is_symlink():
        raise ValueError(f"refuses symlinked source: {source}")
    resolved = _resolve_under_repo(repo_root, "slug escapes repository root", *relative_parts)
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return resolved


def _resolve_under_repo(repo_root: Path, error_message: str, *relative_parts: str) -> Path:
    candidate = (repo_root / Path(*relative_parts)).resolve()
    try:
        candidate.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(error_message) from exc
    return candidate


def _validate_slug(slug: str) -> None:
    slug_path = Path(slug)
    if not slug or slug in {".", ".."}:
        raise ValueError("slug escapes repository root")
    if slug_path.name != slug or len(slug_path.parts) != 1:
        raise ValueError("slug escapes repository root")
