from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .state import Phase, ProductState, evidence_fingerprint, load_state, save_state


PHASE_SEQUENCE: tuple[Phase, ...] = (
    Phase.PLAN_QUERIES,
    Phase.FETCH,
    Phase.DIGEST,
    Phase.PROFILE,
    Phase.VENDOR_SKEPTIC,
    Phase.ARBITER,
    Phase.APPLY,
    Phase.VERIFY,
    Phase.COMPILE,
)
REVIEW_MAX_ROUNDS = 3


@dataclass(frozen=True)
class PhaseOutcome:
    success: bool
    tokens: int = 0
    error: str | None = None
    retry_review: bool = False


@dataclass(frozen=True)
class RunOutcome:
    slug: str
    status: str
    ok: bool
    tokens: int = 0


PhaseHandler = Callable[[str, ProductState], PhaseOutcome]


class GeoLoop:
    def __init__(
        self,
        repo_root: str | Path,
        *,
        phase_handlers: Mapping[Phase, PhaseHandler] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.phase_handlers = dict(phase_handlers or {})

    def run_queue(
        self,
        *,
        limit: int | None = None,
        budget_tokens: int | None = None,
        refresh_stale: int | None = None,
    ) -> list[RunOutcome]:
        outcomes: list[RunOutcome] = []
        spent = 0
        for slug in self._load_queue():
            if limit is not None and len(outcomes) >= limit:
                break
            if budget_tokens is not None and spent >= budget_tokens:
                break
            outcome = self.run_product(slug, refresh_stale=refresh_stale)
            outcomes.append(outcome)
            spent += outcome.tokens
        return outcomes

    def run_product(self, slug: str, *, refresh_stale: int | None = None) -> RunOutcome:
        current_fingerprint = evidence_fingerprint(self.repo_root, slug)
        state = load_state(self.repo_root, slug)

        if state.phase is Phase.PASS:
            if state.evidence_fingerprint == current_fingerprint and not self._is_stale(slug, refresh_stale):
                return RunOutcome(slug=slug, status="skipped", ok=True, tokens=0)
            state = ProductState(slug=slug, evidence_fingerprint=current_fingerprint)
        elif state.evidence_fingerprint not in {None, current_fingerprint}:
            state = ProductState(slug=slug, evidence_fingerprint=current_fingerprint)
        elif state.evidence_fingerprint is None:
            state = ProductState(
                slug=state.slug,
                phase=state.phase,
                round=state.round,
                cost_so_far=state.cost_so_far,
                last_error=state.last_error,
                evidence_fingerprint=current_fingerprint,
            )

        produced_tokens = 0
        while state.phase is not Phase.PASS:
            if state.phase is Phase.VENDOR_SKEPTIC and state.round == 0:
                state = self._replace(state, round=1)

            outcome = self._run_phase(slug, state)
            produced_tokens += outcome.tokens
            state = self._replace(state, cost_so_far=state.cost_so_far + outcome.tokens)

            if outcome.success:
                next_phase = self._next_phase(state.phase)
                if next_phase is Phase.PASS:
                    state = self._replace(state, phase=Phase.PASS, last_error=None)
                    save_state(self.repo_root, state)
                    return RunOutcome(slug=slug, status="passed", ok=True, tokens=produced_tokens)

                if next_phase is Phase.VENDOR_SKEPTIC and state.round == 0:
                    state = self._replace(state, phase=next_phase, round=1, last_error=None)
                else:
                    state = self._replace(state, phase=next_phase, last_error=None)
                save_state(self.repo_root, state)
                continue

            error_message = outcome.error or f"{state.phase.value} failed"
            if state.phase is Phase.VERIFY and outcome.retry_review and state.round < REVIEW_MAX_ROUNDS:
                state = self._replace(
                    state,
                    phase=Phase.VENDOR_SKEPTIC,
                    round=state.round + 1,
                    last_error=error_message,
                )
                save_state(self.repo_root, state)
                continue

            state = self._replace(state, last_error=error_message)
            save_state(self.repo_root, state)
            return RunOutcome(slug=slug, status="failed", ok=False, tokens=produced_tokens)

        save_state(self.repo_root, state)
        return RunOutcome(slug=slug, status="passed", ok=True, tokens=produced_tokens)

    def _load_queue(self) -> list[str]:
        payload = json.loads((self.repo_root / "wiki" / "queue.json").read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("queue.json must contain a list")
        slugs: list[str] = []
        for entry in payload:
            if isinstance(entry, str) and entry:
                slugs.append(entry)
                continue
            if isinstance(entry, dict) and isinstance(entry.get("slug"), str) and entry["slug"]:
                slugs.append(entry["slug"])
                continue
            raise ValueError("queue.json entries must be slugs or objects with slug")
        return slugs

    def _run_phase(self, slug: str, state: ProductState) -> PhaseOutcome:
        handler = self.phase_handlers.get(state.phase)
        if handler is None:
            return PhaseOutcome(success=False, error=f"missing handler for phase: {state.phase.value}")
        try:
            outcome = handler(slug, state)
        except Exception as exc:
            return PhaseOutcome(success=False, error=str(exc))
        return self._coerce_outcome(outcome)

    def _coerce_outcome(self, outcome: Any) -> PhaseOutcome:
        if isinstance(outcome, PhaseOutcome):
            return outcome
        raise TypeError("phase handlers must return PhaseOutcome")

    def _is_stale(self, slug: str, refresh_stale: int | None) -> bool:
        if refresh_stale is None:
            return False
        state_path = self.repo_root / "wiki" / "state" / f"{slug}.json"
        if not state_path.exists():
            return True
        age_seconds = __import__("time").time() - state_path.stat().st_mtime
        return age_seconds >= refresh_stale * 86400

    def _next_phase(self, phase: Phase) -> Phase:
        if phase is Phase.PASS:
            return Phase.PASS
        index = PHASE_SEQUENCE.index(phase)
        if index == len(PHASE_SEQUENCE) - 1:
            return Phase.PASS
        return PHASE_SEQUENCE[index + 1]

    @staticmethod
    def _replace(state: ProductState, **changes: Any) -> ProductState:
        payload = {
            "slug": state.slug,
            "phase": state.phase,
            "round": state.round,
            "cost_so_far": state.cost_so_far,
            "last_error": state.last_error,
            "evidence_fingerprint": state.evidence_fingerprint,
        }
        payload.update(changes)
        return ProductState(**payload)
