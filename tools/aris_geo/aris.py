from __future__ import annotations

import json
import math
import numbers
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


DEFAULT_ALLOWED_TOOLS = ("read_file", "write_file", "glob_search", "grep_search", "Skill")
DEFAULT_MAX_ITERATIONS = 8
REQUIRED_USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)


@dataclass(frozen=True)
class ArisResult:
    message: str
    model: str
    iterations: int
    tool_uses: list[str]
    tool_results: list[Any]
    usage: dict[str, Any]
    raw: dict[str, Any]


def parse_aris_result(
    stdout: str,
    required_tools: Sequence[str] = (),
    *,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> ArisResult:
    try:
        payload = json.loads(stdout, parse_constant=_reject_non_finite_constant)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid ARIS JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("invalid ARIS JSON: top-level object must be a JSON object")

    message = payload.get("message")
    model = payload.get("model")
    iterations = payload.get("iterations")
    tool_uses = payload.get("tool_uses")
    tool_results = payload.get("tool_results")
    usage = payload.get("usage")

    if not isinstance(message, str):
        raise ValueError("invalid ARIS JSON: message must be a string")
    if not isinstance(model, str):
        raise ValueError("invalid ARIS JSON: model must be a string")
    if isinstance(iterations, bool) or not isinstance(iterations, int):
        raise ValueError("invalid ARIS JSON: iterations must be a non-bool integer")
    if not isinstance(tool_uses, list):
        raise ValueError("invalid ARIS JSON: tool_uses must be a list")
    if not isinstance(tool_results, list):
        raise ValueError("invalid ARIS JSON: tool_results must be a list")
    if not isinstance(usage, dict):
        raise ValueError("invalid ARIS JSON: usage must be an object")

    if payload.get("auto_compaction") is not None:
        raise ValueError("ARIS output rejected: auto-compaction is present")
    if iterations > max_iterations:
        raise ValueError(f"ARIS output rejected: iterations exceed {max_iterations}")
    _validate_usage(usage)
    if _has_permission_denied_result(tool_results):
        raise ValueError("ARIS output rejected: permission-denied tool result")

    used_tools = {str(tool) for tool in tool_uses}
    for tool_name in required_tools:
        if tool_name not in used_tools:
            raise ValueError(f"ARIS output rejected: missing required tool: {tool_name}")

    return ArisResult(
        message=message,
        model=model,
        iterations=iterations,
        tool_uses=[str(tool) for tool in tool_uses],
        tool_results=tool_results,
        usage=usage,
        raw=payload,
    )


def run_aris_phase(
    *,
    prompt: str,
    model: str,
    cwd: str | Path,
    runner: Callable[..., Any] = subprocess.run,
    aris_bin: str = "aris",
    allowed_tools: Sequence[str] = DEFAULT_ALLOWED_TOOLS,
    required_tools: Sequence[str] = (),
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> ArisResult:
    cwd_path = Path(cwd)
    argv = [
        aris_bin,
        "--print",
        "--output-format",
        "json",
        "--model",
        model,
        "--permission-mode",
        "workspace-write",
        "--allowedTools",
        ",".join(allowed_tools),
        "--cwd",
        str(cwd_path),
        "prompt",
        prompt,
    ]
    completed = runner(
        argv,
        input="",
        text=True,
        capture_output=True,
        check=False,
        cwd=str(cwd_path),
    )
    if getattr(completed, "returncode", 1) != 0:
        raise ValueError(f"ARIS exited with code {completed.returncode}: {getattr(completed, 'stderr', '')}")
    return parse_aris_result(
        getattr(completed, "stdout", ""),
        required_tools=required_tools,
        max_iterations=max_iterations,
    )


def _has_permission_denied_result(tool_results: list[Any]) -> bool:
    for result in tool_results:
        if _result_has_structured_deny(result):
            return True
        if _result_error_text_has_deny(result):
            return True
    return False


def _validate_usage(usage: dict[str, Any]) -> None:
    for field_name in REQUIRED_USAGE_FIELDS:
        if field_name not in usage:
            raise ValueError(f"invalid ARIS JSON: missing usage field: {field_name}")
        value = usage[field_name]
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            raise ValueError(f"invalid ARIS JSON: usage field {field_name} must be a non-bool number")
        if not math.isfinite(value):
            raise ValueError(f"invalid ARIS JSON: usage field {field_name} must be finite")
        if value < 0:
            raise ValueError(f"invalid ARIS JSON: usage field {field_name} must be non-negative")


def _result_has_structured_deny(result: Any) -> bool:
    if not isinstance(result, dict):
        return False

    status = result.get("status")
    if isinstance(status, str) and status.strip().lower() in {"denied", "permission_denied"}:
        return True

    permission = result.get("permission")
    if isinstance(permission, str) and permission.strip().lower() in {"denied", "permission_denied"}:
        return True

    denied = result.get("denied")
    if isinstance(denied, bool) and denied:
        return True

    error = result.get("error")
    if isinstance(error, dict):
        error_type = error.get("type")
        if isinstance(error_type, str) and error_type.strip().lower() in {"permission_denied", "denied"}:
            return True

    return False


def _result_error_text_has_deny(result: Any) -> bool:
    if not isinstance(result, dict):
        return False
    if result.get("is_error") is not True:
        return False

    for candidate in _iter_error_text_candidates(result):
        haystack = candidate.lower()
        if "permission denied" in haystack:
            return True
        if "denied by policy" in haystack:
            return True
        if "permission_denied" in haystack:
            return True
        if "permission" in haystack and "deny" in haystack:
            return True
    return False


def _iter_error_text_candidates(result: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    for key in ("error", "message", "content"):
        texts.extend(_extract_text(result.get(key)))
    return texts


def _extract_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        texts: list[str] = []
        for nested_value in value.values():
            texts.extend(_extract_text(nested_value))
        return texts
    if isinstance(value, list):
        texts: list[str] = []
        for item in value:
            texts.extend(_extract_text(item))
        return texts
    return []


def _reject_non_finite_constant(value: str) -> Any:
    raise ValueError(f"invalid ARIS JSON: non-finite numeric constant {value}")
