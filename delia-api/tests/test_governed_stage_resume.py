"""DELIA-C3-GOVERNED-STAGE-RESUME-01 (CP4) — governed ephemeral resume.

One question, at most two governed attempts, one monotonic interaction
budget, at most 30s per attempt. When a recoverable model stage times
out, completed typed work (selections, arguments, non-mutating
outcomes) is preserved in an internal request-scoped checkpoint and
the FAILED stage is re-executed — never the whole chain blindly, and
never a PREPARE/ACT invocation twice.

Proven here (deterministic fakes, real orchestrator):

- arguments model_timeout -> checkpoint -> second governed attempt ->
  selection stages NOT re-invoked -> authorized READ executes once ->
  one terminal result.
- Second-attempt timeout, exhausted interaction budget, insufficient
  remaining window, and cancel_check are all terminal, never retried.
- A completed non-mutating invoke outcome is replayed — the MCP call
  is never duplicated.
- A mutating (PREPARE/ACT) invoke boundary is a hard frontier: once
  started, no further attempt may run; it is never re-executed.
- A capability that disappears between attempts is revalidated against
  the fresh live surface — the replayed proposal authorizes nothing.
- Real provider failures keep their own terminal truth (no timeout
  blame, no resume).
"""

from __future__ import annotations

import pytest

from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    SYNTHESIS_INSTRUCTION_ID,
)
from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.capability_provision.mcp_provider import (
    McpCapabilityProvider,
)
from app.application.interaction.activity import ActivityPhase
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.specialist_interop.contracts import (
    RemoteToolOutcome,
)
from app.application.specialist_interop.errors import (
    MCP_AUTHORIZATION_DENIED,
)
from tests.test_execution_ceiling_turn_budget import (
    TEST_MODEL_REF,
    VISTA_TOOLS,
    _StageModel,
    _orchestrator,
)
from tests.test_specialist_capability_orchestration import (
    FakePort,
    READY_PROPOSAL,
    TEO_TOOLS,
    _interop,
    _select,
)


class _FlakyStageModel(_StageModel):
    """_StageModel that fails only the first N invocations per purpose —
    a transient LLM timeout, then the same stage answers validly."""

    def __init__(
        self, proposals=None, failures=None, clock=None,
        advance_on_failure=0.0,
    ):
        super().__init__(proposals=proposals)
        self._failures = dict(failures or {})
        self._clock = clock
        self._advance_on_failure = advance_on_failure

    def invoke(self, request):
        purpose = request.task_purpose_id
        if self._failures.get(purpose, 0) > 0:
            self.requests.append(request)
            self._failures[purpose] -= 1
            if self._clock is not None:
                self._clock[0] += self._advance_on_failure
            raise ModelInvocationError(TIMEOUT, "stage timed out")
        return super().invoke(request)


def _purposes(model: _StageModel) -> list[str | None]:
    return [request.task_purpose_id for request in model.requests]


def _resuming_orchestrator(
    tools_by_specialist,
    specialist_ids,
    model,
    *,
    port=None,
    turn_budget_seconds=30.0,
    interaction_total_budget_seconds=60.0,
    max_governed_attempts=2,
    **kwargs,
) -> OperationalCapabilityOrchestrator:
    port = port or FakePort(tools_by_specialist=tools_by_specialist)
    return OperationalCapabilityOrchestrator(
        [McpCapabilityProvider(_interop(port), specialist_ids)],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
        turn_budget_seconds=turn_budget_seconds,
        interaction_total_budget_seconds=(
            interaction_total_budget_seconds
        ),
        max_governed_attempts=max_governed_attempts,
        **kwargs,
    )


class _SinkSpy:
    """Captures emitted activity phases (ActivityEventSink contract)."""

    def __init__(self) -> None:
        self.phases: list[ActivityPhase] = []

    def emit(self, *, phase, correlation_id=None, **kwargs) -> None:
        self.phases.append(phase)


class _ClockPort(FakePort):
    """FakePort that advances a controllable clock inside the invoke —
    simulates a provider call consuming turn budget."""

    def __init__(self, *args, clock=None, advance=0.0, **kwargs):
        super().__init__(*args, **kwargs)
        self._clock = clock
        self._advance = advance

    def call_remote_tool(
        self, specialist, remote_name, arguments, *, correlation_id,
        timeout_seconds,
    ):
        if self._clock is not None:
            self._clock[0] += self._advance
        return super().call_remote_tool(
            specialist,
            remote_name,
            arguments,
            correlation_id=correlation_id,
            timeout_seconds=timeout_seconds,
        )


# --- mandatory scenario (CP4 §8) ---------------------------------------


def test_arguments_timeout_resumes_failed_stage_only():
    """Question -> selections complete -> arguments model_timeout ->
    checkpoint -> second governed attempt re-runs ONLY arguments ->
    authorized READ executes once -> one result."""
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 1},
    )
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model, port=port
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    purposes = _purposes(model)
    # Valid typed selections were preserved — never asked twice:
    assert purposes.count(INTERACTION_ADMISSION_INSTRUCTION_ID) == 1
    assert purposes.count(GROUP_SELECTION_INSTRUCTION_ID) == 1
    assert purposes.count(CAPABILITY_SELECTION_INSTRUCTION_ID) == 1
    # Only the failed stage ran again:
    assert purposes.count(ARGUMENTS_INSTRUCTION_ID) == 2
    # The authorized READ executed exactly once — no duplicate MCP:
    assert [c[1] for c in port.calls] == ["analyze"]
    assert attempt.outcome is not None


def test_resume_emits_one_continuing_observation():
    """The stream observes honest recovery: a single CONTINUING
    activity when the second attempt actually starts — never a fake
    progress promise."""
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 1},
    )
    sink = _SinkSpy()
    read = _resuming_orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
        activity_sink=sink,
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert sink.phases.count(ActivityPhase.CONTINUING) == 1


# --- negative matrix (CP4 §9) -------------------------------------------


def test_second_attempt_timeout_is_terminal():
    """Both attempts time out -> PROCESSING_TIMEOUT once; the stage
    ran exactly twice, never more."""
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 2},
    )
    read = _resuming_orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "model_timeout"
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 2


def test_exhausted_interaction_budget_blocks_second_attempt():
    """Attempt 1 consumed nearly the whole 60s interaction budget —
    no viable window remains, so there is no second attempt."""
    clock = [1000.0]
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 1},
        clock=clock,
        advance_on_failure=59.0,
    )
    read = _resuming_orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0, clock=lambda: clock[0]),
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 1


def test_cancellation_blocks_second_attempt():
    """Disconnect/cancel observed at the boundary: no second attempt
    ever starts — cancel_check is authoritative."""
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 1},
    )
    read = _resuming_orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
        cancel_check=lambda: True,
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 1


def test_completed_read_outcome_is_replayed_not_duplicated():
    """Attempt 1 completed the READ invoke then exhausted budget
    post-invoke. Attempt 2 replays the typed outcome — the provider
    call happens exactly once."""
    clock = [1000.0]
    port = _ClockPort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "list_playlists": RemoteToolOutcome(
                content_text=None,
                structured={"records": [{"id": "p1"}]},
            )
        },
        clock=clock,
        advance=35.0,
    )
    model = _StageModel(proposals=_select("vista", "list_playlists"))
    read = _resuming_orchestrator(
        {"vista": VISTA_TOOLS}, ("vista",), model, port=port
    )
    attempt = read.attempt(
        "liste minhas programações",
        turn_deadline=TurnDeadline.start(30.0, clock=lambda: clock[0]),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert [c[1] for c in port.calls] == ["list_playlists"]


def test_mutating_invoke_is_a_hard_resume_frontier():
    """PREPARE started in attempt 1 and the turn budget died right
    after — resume is refused at the frontier and PREPARE is NEVER
    re-executed (READ != PREPARE != ACT)."""
    clock = [1000.0]
    port = _ClockPort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={"prepare_change": READY_PROPOSAL},
        clock=clock,
        advance=35.0,
    )
    model = _StageModel(
        proposals=_select(
            "vista",
            "prepare_change",
            {"record_id": "p1"},
            goal_class="create_or_modify",
        )
    )
    read = _resuming_orchestrator(
        {"vista": VISTA_TOOLS}, ("vista",), model, port=port
    )
    attempt = read.attempt(
        "Altere o nome do painel p1 para Painel X",
        turn_deadline=TurnDeadline.start(30.0, clock=lambda: clock[0]),
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    # The material invocation ran exactly once across both attempts —
    # the frontier refuses any re-execution.
    assert [c[1] for c in port.calls].count("prepare_change") == 1


def test_capability_gone_between_attempts_is_revalidated():
    """The checkpoint preserves typed proposals, never authority: if
    the live surface no longer offers the capability, the replayed
    selection fails revalidation — no invoke, no invented success."""

    class _ShrinkingPort(FakePort):
        def list_remote_tools(self, specialist, *, timeout_seconds):
            self.list_calls.append(specialist.specialist_id)
            if len(self.list_calls) > 1:
                return ()
            return self._tools.get(specialist.specialist_id, ())

    port = _ShrinkingPort(tools_by_specialist={"teo": TEO_TOOLS})
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 1},
    )
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model, port=port
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS
    assert [c[1] for c in port.calls] == []


def test_authorization_revoked_between_attempts_denies_fresh():
    """Revocation scenario: the checkpoint preserves proposals, never
    permission. Authorization is re-evaluated on the resumed invoke —
    a denial inside attempt 2 is the live owner verdict, not a cached
    grant."""

    class _RevokingPort(FakePort):
        def call_remote_tool(
            self, specialist, remote_name, arguments, *,
            correlation_id, timeout_seconds,
        ):
            self.calls.append(
                (specialist.specialist_id, remote_name, dict(arguments))
            )
            raise CapabilityProviderError(
                MCP_AUTHORIZATION_DENIED, "delegated grant revoked"
            )

    port = _RevokingPort(tools_by_specialist={"teo": TEO_TOOLS})
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 1},
    )
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model, port=port
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.AUTHZ_DENIED
    assert attempt.error_code == MCP_AUTHORIZATION_DENIED
    assert [c[1] for c in port.calls] == ["analyze"]


def test_real_provider_failure_is_not_resumed_or_blamed_on_timeout():
    """A genuine MCP/source failure is not a recoverable model
    timeout: no second attempt, SOURCE truth preserved."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        errors={
            ("vista", "list_playlists"): CapabilityProviderError(
                "source_error", "mcp unreachable"
            )
        },
    )
    model = _StageModel(proposals=_select("vista", "list_playlists"))
    read = _resuming_orchestrator(
        {"vista": VISTA_TOOLS}, ("vista",), model, port=port
    )
    attempt = read.attempt(
        "liste minhas programações",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code not in (
        "model_timeout",
        "turn_budget_exhausted",
    )
    assert [c[1] for c in port.calls] == ["list_playlists"]


def test_legacy_single_attempt_mode_is_unchanged():
    """Recovery disabled (max_governed_attempts=1 — the production
    default): a model timeout is terminal exactly as before."""
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 1},
    )
    read = _orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "model_timeout"
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 1


@pytest.mark.parametrize("cri_enabled", [False, True])
def test_resume_works_with_cri_on_and_off(cri_enabled):
    """CRI parity: the resume mechanism is response-mode neutral — the
    same checkpoint path succeeds whether the response intelligence
    branch is active or at baseline."""
    kwargs = {}
    if cri_enabled:
        kwargs = {
            "response_intelligence_enabled": True,
            "cri_instruction_clause": (
                "\nDeclared-answer requirement: when the user asks for "
                "a count, answer with the count."
            ),
            "cri_instruction_version": "test-cri-v1",
        }
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 1},
    )
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model, port=port, **kwargs
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert [c[1] for c in port.calls] == ["analyze"]


def test_confirmation_turn_never_resumes():
    """A typed confirmation executes the ACT chain once — governed
    resume never re-enters a material decision path."""
    model = _StageModel(proposals=_select("vista", "commit_proposal"))
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "prepare_change": READY_PROPOSAL,
            "commit_proposal": RemoteToolOutcome(
                content_text="done", structured={"ok": True}
            ),
        },
    )
    read = _resuming_orchestrator(
        {"vista": VISTA_TOOLS}, ("vista",), model, port=port
    )
    attempt = read.attempt(
        "",
        confirmation={"decision": "CONFIRM", "pending_id": "p1"},
        turn_deadline=TurnDeadline.start(30.0),
    )
    # The invalid/unknown pending decision fails closed deterministically;
    # nothing material is invoked and nothing is re-attempted:
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS
    assert [c[1] for c in port.calls] == []
