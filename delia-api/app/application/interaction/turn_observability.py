"""Turn-level model-usage observability — request-scoped, bounded.

DELIA-UX-CONTEXT-PANEL-EVIDENCE-ACTIVITY-AND-LLM-USAGE-INTEGRATION-01
(Prompt 5): ``ModelInvocationResult`` already carries provider-reported
usage (``UsageMetadata``) and the real measured stage duration — both
were produced at the invocation boundary and then discarded. One
bounded request-scoped ledger collects them at the two real call sites
(the orchestrator's shared ``_model_stage_proposal`` funnel and the
handler's conversational ``_invoke``) so the terminal ``turn_result``
can expose honest, presentation-only numbers.

Hard rules honoured here:

- A replayed governed-resume proposal is data, not a new model call —
  only real ``InvokeModel.execute`` completions/errors enter the ledger.
- A failed or timed-out call never fabricates usage: it is counted as
  a call, its token fields stay absent, and the aggregate degrades to
  ``partial``/``unavailable`` instead of pretending zero.
- Deterministic revalidation, owner invocations and MCP payloads are
  never counted — tokens belong to the model boundary only.
- This is an observation projection, never authority, cost truth, or
  a second telemetry engine: no persistence, no aggregation across
  turns, no pricing.
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import Any, Mapping

from app.application.model_invocation.contracts import ModelInvocationResult
from app.domain.evidence.model import ModelRef


# Bounded disclosure mirrors ActivityEvent's scale: stage identity is a
# stable technical id, never free text.
MAX_STAGE_CHARS = 160
# Bounded ledger — a turn has a small fixed set of model stages; the cap
# exists only so a pathological loop can never grow memory unboundedly.
MAX_LEDGER_CALLS = 24

# Effective composition of the answer the user received — requested vs
# effective stay distinct (a startup flag is never proof of use).
COMPOSITION_CRI = "cri"
COMPOSITION_DETERMINISTIC = "deterministic"
COMPOSITION_MODEL = "model"

# Usage provenance — the only vocabulary the UI may distinguish. The
# wire contract must not carry provider identity (canonical leak gate),
# so a fully reported set is ``reported``, never provider-named.
USAGE_STATUS_REPORTED = "reported"
USAGE_STATUS_PARTIAL = "partial"
USAGE_STATUS_UNAVAILABLE = "unavailable"

# Coarse finish vocabulary — the raw InvocationFinishStatus enum may
# name provider-level semantics; the public projection keeps only the
# operational fact the user needs.
_FINISH_COMPLETED = "completed"
_FINISH_TIMEOUT = "timeout"
_FINISH_ERROR = "error"


def _finish_label(finish_status: Any) -> str:
    name = getattr(finish_status, "value", finish_status)
    if not isinstance(name, str):
        return _FINISH_ERROR
    lowered = name.lower()
    if lowered == "completed":
        return _FINISH_COMPLETED
    if "timeout" in lowered:
        return _FINISH_TIMEOUT
    return _FINISH_ERROR


def _bounded_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text[:MAX_STAGE_CHARS] if text else None


def _bounded_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if value >= 0 else None


@dataclass(frozen=True, slots=True)
class ModelCallObservation:
    """One real model invocation observed during this turn."""

    stage: str
    attempt: int
    finish_status: str
    duration_ms: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    # Stage-6 budget attribution: interaction budget still available
    # when this stage was granted its timeout — starvation evidence,
    # never a scheduling decision input.
    budget_remaining_ms: int | None = None
    # Context Intelligence WP-F: pre-call budget decision carried from
    # ModelInvocationResult/ModelInvocationError — estimates labeled as
    # estimates, provider usage stays the only actual count.
    error_code: str | None = None
    instruction_version: str | None = None
    context_window_tokens: int | None = None
    input_chars: int | None = None
    estimated_input_tokens: int | None = None
    generation_reserve_tokens: int | None = None
    prior_turns_included: int | None = None
    prior_turns_omitted: int | None = None
    context_reduction_reason: str | None = None
    context_budget_status: str | None = None

    def to_projection(self) -> dict[str, Any]:
        return {
            "stage": _bounded_text(self.stage),
            "attempt": _bounded_int(self.attempt),
            "finish_status": _bounded_text(self.finish_status),
            "duration_ms": _bounded_int(self.duration_ms),
            "input_tokens": _bounded_int(self.input_tokens),
            "output_tokens": _bounded_int(self.output_tokens),
            "budget_remaining_ms": _bounded_int(
                self.budget_remaining_ms
            ),
            "error_code": _bounded_text(self.error_code),
            # Projected as lineage_version: the instruction lineage
            # version — the response surface must never carry the
            # term "instruction" (leak guard).
            "lineage_version": _bounded_text(
                self.instruction_version
            ),
            "context_window_tokens": _bounded_int(
                self.context_window_tokens
            ),
            "input_chars": _bounded_int(self.input_chars),
            "estimated_input_tokens": _bounded_int(
                self.estimated_input_tokens
            ),
            "generation_reserve_tokens": _bounded_int(
                self.generation_reserve_tokens
            ),
            "prior_turns_included": _bounded_int(
                self.prior_turns_included
            ),
            "prior_turns_omitted": _bounded_int(
                self.prior_turns_omitted
            ),
            "context_reduction_reason": _bounded_text(
                self.context_reduction_reason
            ),
            "context_budget_status": _bounded_text(
                self.context_budget_status
            ),
        }


@dataclass(frozen=True, slots=True)
class OperationalCallObservation:
    """One owner-surface invocation observed during this turn —
    capability execution time separated from model decision time."""

    capability: str
    duration_ms: int | None = None
    finish_status: str = _FINISH_COMPLETED

    def to_projection(self) -> dict[str, Any]:
        return {
            "capability": _bounded_text(self.capability),
            "duration_ms": _bounded_int(self.duration_ms),
            "finish_status": _bounded_text(self.finish_status),
        }


# Coarse terminal timeout attribution — the wire never distinguishes
# transport internals, only which responsibility consumed the budget.
_TIMEOUT_SOURCES = frozenset(
    {"model", "budget", "capability", "cancelled"}
)


class ModelCallLedger:
    """Bounded request-scoped collector — one per interaction turn.

    Mutable by design and confined to the executing context (ContextVar);
    the orchestrator instance is shared across concurrent turns so this
    state can never live on it.
    """

    __slots__ = (
        "_calls",
        "_operational",
        "_timeout_source",
        "_composition_ms",
    )

    def __init__(self) -> None:
        self._calls: list[ModelCallObservation] = []
        self._operational: list[OperationalCallObservation] = []
        self._timeout_source: str | None = None
        self._composition_ms: int = 0

    @property
    def calls(self) -> tuple[ModelCallObservation, ...]:
        return tuple(self._calls)

    @property
    def operational_calls(
        self,
    ) -> tuple[OperationalCallObservation, ...]:
        return tuple(self._operational)

    @property
    def timeout_source(self) -> str | None:
        return self._timeout_source

    @property
    def composition_ms(self) -> int:
        return self._composition_ms

    def _append(self, observation: ModelCallObservation) -> None:
        if len(self._calls) >= MAX_LEDGER_CALLS:
            return
        self._calls.append(observation)

    def record_result(
        self,
        *,
        stage: str,
        result: ModelInvocationResult,
        attempt: int = 1,
        budget_remaining_ms: int | None = None,
    ) -> None:
        """Record a real completed model call — provider usage verbatim,
        never inferred."""
        usage = result.usage
        budget = getattr(result, "context_budget", None)
        lineage = getattr(result, "lineage", None)
        instruction_lineage = (
            getattr(lineage, "instruction_lineage", None)
            if lineage is not None
            else None
        )
        self._append(
            ModelCallObservation(
                stage=stage,
                attempt=attempt,
                finish_status=_finish_label(result.finish_status),
                duration_ms=result.duration_ms,
                input_tokens=(
                    usage.input_units if usage is not None else None
                ),
                output_tokens=(
                    usage.output_units if usage is not None else None
                ),
                budget_remaining_ms=budget_remaining_ms,
                instruction_version=(
                    instruction_lineage.version
                    if instruction_lineage is not None
                    else None
                ),
                context_window_tokens=(
                    budget.context_window_tokens if budget else None
                ),
                input_chars=budget.input_chars if budget else None,
                estimated_input_tokens=(
                    budget.estimated_input_tokens if budget else None
                ),
                generation_reserve_tokens=(
                    budget.generation_reserve_tokens if budget else None
                ),
                prior_turns_included=(
                    budget.prior_turns_included if budget else None
                ),
                prior_turns_omitted=(
                    budget.prior_turns_omitted if budget else None
                ),
                context_reduction_reason=(
                    budget.reduction_reason if budget else None
                ),
                context_budget_status=(
                    budget.budget_status if budget else None
                ),
            )
        )

    def record_error(
        self,
        *,
        stage: str,
        finish_status: str,
        attempt: int = 1,
        duration_ms: int | None = None,
        budget_remaining_ms: int | None = None,
        error_code: str | None = None,
        context_budget: Any = None,
    ) -> None:
        """Record a real model call that failed or timed out — counted
        as a call, token fields stay absent (never fabricated)."""
        self._append(
            ModelCallObservation(
                stage=stage,
                attempt=attempt,
                finish_status=_finish_label(finish_status),
                duration_ms=duration_ms,
                budget_remaining_ms=budget_remaining_ms,
                error_code=error_code,
                context_window_tokens=(
                    context_budget.context_window_tokens
                    if context_budget is not None
                    else None
                ),
                input_chars=(
                    context_budget.input_chars
                    if context_budget is not None
                    else None
                ),
                estimated_input_tokens=(
                    context_budget.estimated_input_tokens
                    if context_budget is not None
                    else None
                ),
                generation_reserve_tokens=(
                    context_budget.generation_reserve_tokens
                    if context_budget is not None
                    else None
                ),
                prior_turns_included=(
                    context_budget.prior_turns_included
                    if context_budget is not None
                    else None
                ),
                prior_turns_omitted=(
                    context_budget.prior_turns_omitted
                    if context_budget is not None
                    else None
                ),
                context_reduction_reason=(
                    context_budget.reduction_reason
                    if context_budget is not None
                    else None
                ),
                context_budget_status=(
                    context_budget.budget_status
                    if context_budget is not None
                    else None
                ),
            )
        )

    def record_operational(
        self,
        *,
        capability: str,
        duration_ms: int | None,
        finish_status: str,
    ) -> None:
        """Record a real owner-surface invocation — the operational
        share of the interaction budget, separated from model time."""
        if len(self._operational) >= MAX_LEDGER_CALLS:
            return
        self._operational.append(
            OperationalCallObservation(
                capability=capability,
                duration_ms=duration_ms,
                finish_status=_finish_label(finish_status),
            )
        )

    def record_terminal_timeout(self, source: str) -> None:
        """Attribute the terminal timeout once, at the attempt
        boundary — coarse responsibility vocabulary only."""
        if source in _TIMEOUT_SOURCES and self._timeout_source is None:
            self._timeout_source = source

    def record_composition(self, duration_ms: int) -> None:
        """Accumulate deterministic composition time (CRI selection/
        render) — never a model call."""
        if isinstance(duration_ms, int) and duration_ms > 0:
            self._composition_ms += duration_ms


# Request-scoped binding — same ContextVar pattern as the activity sink
# and the resume checkpoint. Absent → observation silently off (legacy
# in-process callers behave exactly like before).
_TURN_CALL_LEDGER: contextvars.ContextVar[ModelCallLedger | None] = (
    contextvars.ContextVar("delia_turn_call_ledger", default=None)
)


def bind_turn_call_ledger(
    ledger: ModelCallLedger,
) -> contextvars.Token:
    return _TURN_CALL_LEDGER.set(ledger)


def reset_turn_call_ledger(token: contextvars.Token) -> None:
    _TURN_CALL_LEDGER.reset(token)


def current_call_ledger() -> ModelCallLedger | None:
    return _TURN_CALL_LEDGER.get()


def aggregate_usage(
    calls: tuple[ModelCallObservation, ...],
) -> dict[str, Any]:
    """Sum only provider-reported numbers — honest partial semantics.

    ``reported`` only when every recorded call carried both
    directions; ``partial`` when at least one number exists; otherwise
    ``unavailable``. Totals are the sum of the reported directions —
    never an invented global figure.
    """
    input_sum = 0
    output_sum = 0
    input_seen = 0
    output_seen = 0
    complete = 0
    for call in calls:
        has_input = call.input_tokens is not None
        has_output = call.output_tokens is not None
        if has_input:
            input_sum += int(call.input_tokens or 0)
            input_seen += 1
        if has_output:
            output_sum += int(call.output_tokens or 0)
            output_seen += 1
        if has_input and has_output:
            complete += 1
    if not calls or (input_seen == 0 and output_seen == 0):
        return {
            "status": USAGE_STATUS_UNAVAILABLE,
            "input": None,
            "output": None,
            "total": None,
        }
    # ``total`` is claimed only when every recorded call reported both
    # directions — a partial sum presented as a total would fabricate
    # completeness. Each direction is shown only when actually reported.
    fully_reported = complete == len(calls)
    return {
        "status": (
            USAGE_STATUS_REPORTED
            if fully_reported
            else USAGE_STATUS_PARTIAL
        ),
        "input": input_sum if input_seen else None,
        "output": output_sum if output_seen else None,
        "total": (input_sum + output_sum) if fully_reported else None,
    }


def build_turn_observability(
    *,
    model_ref: ModelRef | None,
    response_mode: str,
    composition_mode: str,
    calls: tuple[ModelCallObservation, ...],
    duration_ms: int | None,
    governed_attempts: int,
    operational_calls: tuple[OperationalCallObservation, ...] = (),
    timeout_source: str | None = None,
    composition_ms: int = 0,
) -> dict[str, Any]:
    """Bounded presentation-only projection for ``turn_result``.

    Identity fields only on the model block — never endpoint URLs,
    credentials, instruction bodies or provider identity (the canonical
    response leak gate forbids the provider surface; owner is the
    honest, exposable attribution). ``cost`` is explicitly unavailable:
    no provider in the current chain reports billing data and no
    versioned price table exists, so the honest answer is stated
    rather than estimated.

    Stage 6 budget attribution: ``elapsed_ms`` splits the measured
    interaction time by responsibility — ``model`` (semantic decision
    stages), ``operational`` (owner capability execution incl.
    transport), ``composition`` (deterministic CRI/render) and
    ``other`` (orchestration glue, validation, waits). ``None`` fields
    mean "not measured", never zero. ``timeout_source`` attributes a
    terminal timeout once, in coarse responsibility terms — a model
    timeout is never relabelled as an owner-API failure.
    """
    model: dict[str, Any] | None = None
    if model_ref is not None:
        model = {
            "id": _bounded_text(model_ref.model_id),
            "version": _bounded_text(model_ref.version),
            "owner": _bounded_text(model_ref.owner_ref),
        }
    model_ms = sum(
        call.duration_ms for call in calls if call.duration_ms is not None
    )
    operational_ms = sum(
        call.duration_ms
        for call in operational_calls
        if call.duration_ms is not None
    )
    elapsed: dict[str, Any] = {
        "model": model_ms,
        "operational": operational_ms,
        "composition": composition_ms,
        "other": (
            max(0, duration_ms - model_ms - operational_ms - composition_ms)
            if duration_ms is not None
            else None
        ),
    }
    return {
        "model": model,
        "response_mode": _bounded_text(response_mode),
        "composition_mode": _bounded_text(composition_mode),
        "duration_ms": _bounded_int(duration_ms),
        "governed_attempts": _bounded_int(governed_attempts),
        "model_calls": len(calls),
        "calls": [call.to_projection() for call in calls],
        "operational_calls": [
            call.to_projection() for call in operational_calls
        ],
        "elapsed_ms": elapsed,
        "timeout_source": (
            _bounded_text(timeout_source)
            if timeout_source in _TIMEOUT_SOURCES
            else None
        ),
        "tokens": aggregate_usage(calls),
        "cost": {"status": "unavailable"},
    }
