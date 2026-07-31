from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence


DEFAULT_ALLOWED_TOOLS = ("read_file", "write_file", "glob_search", "grep_search", "Skill")
DEFAULT_MAX_ITERATIONS = 8


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
        payload = json.loads(stdout)
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
    if not isinstance(iterations, int):
        raise ValueError("invalid ARIS JSON: iterations must be an integer")
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
        haystack = _flatten_result_text(result)
        if "permission denied" in haystack:
            return True
        if "denied by policy" in haystack:
            return True
        if "permission_denied" in haystack:
            return True
        if "permission" in haystack and "deny" in haystack:
            return True
    return False


def _flatten_result_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    except TypeError:
        return str(value).lower()
