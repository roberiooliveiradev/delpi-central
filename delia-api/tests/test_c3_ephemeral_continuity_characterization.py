"""DELIA-C3-EPHEMERAL-CONTINUITY-AND-LLM-RECOVERY-INVENTORY-01 — ETAPA H.

Characterization only: these tests OBSERVE the current boundary so the
continuity decision rests on measured facts, not inference. They change
no runtime behavior.

Measured facts asserted here:

- When a model stage times out, ``attempt()`` returns
  PROCESSING_TIMEOUT carrying ONLY status/correlation/error_code —
  every completed upstream result (group, capability, arguments,
  verified MCP outcome) dies with the ``_attempt`` frame. The data
  exists as locals at the raise site but is never exported.
- A transient non-timeout provider error is a SOFT degradation
  (stage returns None) — it never reaches the terminal timeout path.
- The remaining-budget math determines whether an in-request bounded
  retry could even start: ``deadline.stage_timeout`` must stay
  >= MIN_VIABLE_MODEL_STAGE_SECONDS.
- The MCP invoke request carries no idempotency key — a resumed
  attempt that re-invoked a completed call would duplicate the READ
  (harmless) and would be fatal for ACT-class work (must never
  resume past a completed PREPARE/ACT).
"""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    MIN_VIABLE_MODEL_STAGE_SECONDS,
    SYNTHESIS_INSTRUCTION_ID,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.errors import ModelInvocationError
from app.application.specialist_interop.contracts import (
    RemoteToolOutcome,
)
from tests.test_execution_ceiling_turn_budget import (
    VISTA_TOOLS,
    _StageModel,
    _deadline,
    _orchestrator,
)
from tests.test_specialist_capability_orchestration import (
    FakePort,
    TEO_TOOLS,
    _interop,
    _read,
    _select,
)


MODEL_TIMEOUT = "stage timed out"


def _purposes(model: _StageModel) -> list[str | None]:
    return [request.task_purpose_id for request in model.requests]


# --- state-loss boundary ------------------------------------------------


def test_arguments_timeout_discards_completed_selection_work():
    """Selection stages completed; the arguments stage timed out. The
    terminal attempt proves completed work is never exported — it
    exists only as ``_attempt`` locals at the raise site."""
    model = _StageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        timeout_purposes=frozenset({ARGUMENTS_INSTRUCTION_ID}),
    )
    read = _orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(80.0),
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "model_timeout"
    # The completed stages actually ran before the loss:
    assert INTERACTION_ADMISSION_INSTRUCTION_ID in _purposes(model)
    assert GROUP_SELECTION_INSTRUCTION_ID in _purposes(model)
    assert CAPABILITY_SELECTION_INSTRUCTION_ID in _purposes(model)
    assert ARGUMENTS_INSTRUCTION_ID in _purposes(model)
    # …and none of their results escape the boundary:
    assert attempt.outcome is None
    assert attempt.provenance is None
    assert attempt.owner_hint is None
    assert attempt.content is None


def test_synthesis_timeout_uses_existing_deterministic_fallback():
    """Post-invoke model timeouts are ALREADY recoverable: the
    synthesis stage degrades to deterministic rendering of the
    verified outcome — SUCCESS is preserved, evidence is not lost.
    This is the existing recovery pattern a resume mechanism must
    match, not a gap."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "list_playlists": RemoteToolOutcome(
                content_text=None,
                structured={"records": [{"id": "p1"}]},
            )
        },
    )
    model = _StageModel(
        proposals=_select("vista", "list_playlists"),
        timeout_purposes=frozenset({SYNTHESIS_INSTRUCTION_ID}),
    )
    read = _orchestrator(
        {"vista": VISTA_TOOLS}, ("vista",), model, port=port
    )
    attempt = read.attempt(
        "liste minhas programações",
        turn_deadline=TurnDeadline.start(80.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert [c[1] for c in port.calls] == ["list_playlists"]
    assert attempt.outcome is not None
    assert attempt.content


def test_admission_timeout_degrades_to_selection():
    """The admission stage already recovers: a timed-out admission is
    treated as inconclusive and the chain proceeds to provider
    selection — an existing in-flight degradation, not a terminal
    timeout and never an invented conversational skip."""
    port = FakePort(tools_by_specialist={"vista": VISTA_TOOLS})
    model = _StageModel(
        proposals=_select("vista", "list_playlists"),
        timeout_purposes=frozenset({INTERACTION_ADMISSION_INSTRUCTION_ID}),
    )
    read = _orchestrator(
        {"vista": VISTA_TOOLS}, ("vista",), model, port=port
    )
    attempt = read.attempt(
        "liste minhas programações",
        turn_deadline=TurnDeadline.start(80.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert INTERACTION_ADMISSION_INSTRUCTION_ID in _purposes(model)
    assert GROUP_SELECTION_INSTRUCTION_ID in _purposes(model)
    assert [c[1] for c in port.calls] == ["list_playlists"]


def test_transient_provider_error_is_soft_degradation_not_timeout():
    """Case F: a non-timeout ModelInvocationError returns None from the
    stage — the chain degrades honestly instead of terminating."""
    model = _StageModel(
        proposals=_select("vista", "list_playlists"),
        timeout_purposes=frozenset({GROUP_SELECTION_INSTRUCTION_ID}),
    )
    # Override the error code: transient provider failure, not TIMEOUT.
    original_invoke = model.invoke

    def transient(request):
        if request.task_purpose_id == GROUP_SELECTION_INSTRUCTION_ID:
            raise ModelInvocationError("UNAVAILABLE", "provider 503")
        return original_invoke(request)

    model.invoke = transient  # type: ignore[method-assign]
    read = _orchestrator(
        {"vista": VISTA_TOOLS}, ("vista",), model
    )
    attempt = read.attempt(
        "liste minhas programações",
        turn_deadline=TurnDeadline.start(80.0),
    )
    # Soft degradation — never a false timeout, never source-blame.
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert attempt.error_code is None


# --- retry-window characterization (existing math, no new behavior) -----


def test_in_budget_retry_window_exists_after_early_stage_failure():
    """When a stage fails fast with budget remaining, the same shared
    deadline still grants a viable timeout — the in-request retry seam
    needs no new budget object."""
    clock = [1000.0]
    deadline = _deadline(clock, 30.0)
    # A stage consumed 21s then errored — 9s remain.
    clock[0] += 21.0
    retry_budget = deadline.stage_timeout(30.0)
    assert retry_budget >= MIN_VIABLE_MODEL_STAGE_SECONDS
    assert deadline.remaining_seconds() == 9.0


def test_no_retry_window_once_turn_budget_is_exhausted():
    """The same shared deadline honestly refuses a second stage once
    the total budget is gone — in-request retry cannot bypass it."""
    clock = [1000.0]
    deadline = _deadline(clock, 30.0)
    clock[0] += 31.0
    assert deadline.stage_timeout(30.0) == 0.0
    assert deadline.exhausted()


# --- idempotency gap characterization ------------------------------------


def test_invoke_request_carries_no_idempotency_key():
    """Resuming past a completed invoke would re-issue the call — the
    wire contract has no dedupe/idempotency field. For READ-class that
    is at worst a repeated read; for PREPARE/ACT any resume must be
    forbidden before the invoke frontier."""
    seen: list[tuple] = []

    class _SpyPort(FakePort):
        def call_remote_tool(
            self, specialist, remote_name, arguments, *, correlation_id,
            timeout_seconds,
        ):
            seen.append((remote_name, correlation_id))
            return super().call_remote_tool(
                specialist,
                remote_name,
                arguments,
                correlation_id=correlation_id,
                timeout_seconds=timeout_seconds,
            )

    port = _SpyPort(tools_by_specialist={"vista": VISTA_TOOLS})
    read = _read(
        _interop(port),
        specialist_ids=("vista",),
        proposal=_select("vista", "list_playlists"),
    )
    attempt = read.attempt("liste minhas programações")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert len(seen) == 1


# Not executable here (require a live transport or a second attempt that
# does not exist yet): client_disconnect_during_retry, double_terminal
# delivery, cancellation mid-resume. Recorded as TEST_NOT_RUN in the
# inventory report — the NDJSON worker contract (GeneratorExit → worker
# finishes bounded, never re-executed) is documented at
# app/interfaces/http/interaction_routes.py.
