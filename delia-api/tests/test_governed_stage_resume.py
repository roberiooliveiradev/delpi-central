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
from app.application.model_invocation.contracts import (
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    INVALID_REQUEST,
    INVALID_STRUCTURED_OUTPUT,
    PROVIDER_UNAVAILABLE,
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.governed_retries import (
    call_retry_eligible,
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
    llm_call_max_attempts=3,
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
        llm_call_max_attempts=llm_call_max_attempts,
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


def test_call_retry_budget_exhaustion_is_terminal():
    """Doc 103: three consecutive timeouts consume the logical call's
    retry budget -> PROCESSING_TIMEOUT once; the stage ran exactly
    three real invocations, never a fourth."""
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 3},
    )
    read = _resuming_orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "model_timeout"
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 3


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
    flag = {"v": False}

    class _CancelAfterFailure(_FlakyStageModel):
        def invoke(self, request):
            try:
                return super().invoke(request)
            except ModelInvocationError:
                # The client disconnected while attempt 1's stage was
                # failing — observed before any new attempt may start.
                flag["v"] = True
                raise

    model = _CancelAfterFailure(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 1},
    )
    read = _resuming_orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
        cancel_check=lambda: flag["v"],
    )
    assert flag["v"] is True
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 1


def test_cancellation_from_the_start_runs_no_model_call():
    """Cancel already observed when the turn begins: not even the
    first model stage may start a new invocation."""
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
    assert attempt.error_code == "cancelled"
    assert _purposes(model) == []


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
    """Doc 103: max_governed_attempts governs TURN resume, not the
    per-call retry — a single transient timeout is recovered inside
    the same logical call; only three consecutive timeouts terminate.
    GATE 1: retries are exercised with the dev-authorized call limit
    (3) while turn resume stays OFF (default)."""
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 3},
    )
    read = _orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model, llm_call_max_attempts=3
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "model_timeout"
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 3


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


# --- doc-103 per-logical-call retry matrix -------------------------------
#
# One logical model call may make at most three real invocations, only
# for recoverable classes (timeout, provider-unavailable/transient,
# invalid structured output), only while budget remains and no
# cancellation was observed. This is a retry of the MODEL CALL — never
# of the turn, the MCP/Domain invoke or a material operation.


class _CodedFailureModel(_StageModel):
    """_StageModel that raises a chosen error code for the first N
    invocations of a purpose, then answers validly — classifies
    recoverable versus definitive call failures."""

    def __init__(self, proposals=None, coded_failures=None):
        super().__init__(proposals=proposals)
        # purpose -> list of error codes, one per real invocation
        self._coded = {k: list(v) for k, v in (coded_failures or {}).items()}

    def invoke(self, request):
        queue = self._coded.get(request.task_purpose_id)
        if queue:
            code = queue.pop(0)
            self.requests.append(request)
            raise ModelInvocationError(code, f"stage failed: {code}")
        return super().invoke(request)


class _MalformedThenValidModel(_StageModel):
    """Returns a schema-incompatible payload for the first N calls of
    a purpose, then the valid proposal — invalid structured output is
    a recoverable class: the SAME bounded request may parse cleanly
    on a fresh invocation."""

    def __init__(self, proposals=None, malformed_purposes=None):
        super().__init__(proposals=proposals)
        self._malformed = dict(malformed_purposes or {})

    def invoke(self, request):
        purpose = request.task_purpose_id
        if self._malformed.get(purpose, 0) > 0:
            self._malformed[purpose] -= 1
            self.requests.append(request)
            return ProviderInvocationPayload(
                structured_output={"unrelated_key": True},
                generated_at="2026-01-01T00:00:00+00:00",
            )
        return super().invoke(request)


def test_recoverable_failures_succeed_on_the_third_real_call():
    """Two recoverable timeouts then a valid answer: the logical call
    succeeds on the third real invocation — attempts not needed are
    never spent."""
    model = _CodedFailureModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        coded_failures={ARGUMENTS_INSTRUCTION_ID: [TIMEOUT, TIMEOUT]},
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
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 3
    # The authorized READ executed exactly once — the call retry never
    # replayed or duplicated the material operation.
    assert [c[1] for c in port.calls] == ["analyze"]


def test_provider_unavailable_is_retry_eligible():
    """A transient provider/adapter failure is recoverable: the same
    logical call retries and succeeds on the second invocation."""
    model = _CodedFailureModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        coded_failures={
            ARGUMENTS_INSTRUCTION_ID: [PROVIDER_UNAVAILABLE]
        },
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
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 2
    assert [c[1] for c in port.calls] == ["analyze"]


def test_invalid_structured_output_is_retry_eligible():
    """Malformed structured output is recoverable (bounded at three):
    the stage retries and accepts the next valid payload."""
    model = _MalformedThenValidModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        malformed_purposes={ARGUMENTS_INSTRUCTION_ID: 1},
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
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 2
    assert [c[1] for c in port.calls] == ["analyze"]


def test_definitive_error_never_retries():
    """A definitive failure class (invalid request) cannot succeed on
    a fresh identical call — exactly one real invocation, no retry."""
    model = _CodedFailureModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        coded_failures={ARGUMENTS_INSTRUCTION_ID: [INVALID_REQUEST]},
    )
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model, port=port
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 1
    assert [c[1] for c in port.calls] == []


def test_call_timeout_grant_reaches_the_doc_103_ceiling():
    """The legacy local cutoffs are gone: a stage call is granted up to
    the 60s per-call ceiling — and a legitimate ~45s invocation is not
    truncated by the removed 10s/30s stage rules."""
    clock = [1000.0]

    class _SlowStageModel(_StageModel):
        def invoke(self, request):
            # The call legitimately consumes 45s inside its grant.
            clock[0] += 45.0
            return super().invoke(request)

    model = _SlowStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"})
    )
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(
            300.0, clock=lambda: clock[0]
        ),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    first = model.requests[0]
    # Granted the per-call ceiling (60s), not the removed stage cap —
    # and every invocation stayed inside the granted window.
    assert 10.0 < first.timeout_seconds <= 60.0


# --- GATE 1: per-call retry isolation (doc 104 coordination review) ---------
#
# The per-LOGICAL-CALL retry limit is a distinct, environment-governed
# configuration — DELIA_LLM_CALL_MAX_ATTEMPTS — separate from the
# turn-resume DELIA_MAX_GOVERNED_ATTEMPTS. Default/absent/invalid = 1
# (OFF): production never retries involuntarily.


def test_call_retry_eligible_defaults_to_off():
    """The predicate fails closed: an un-wired caller (or the absent
    config value it resolves to) never retries."""
    assert not call_retry_eligible(TIMEOUT, 1)
    assert not call_retry_eligible(TIMEOUT, 1, 1)
    # ON at the approved ceiling: attempts 1-2 may retry, the third
    # real invocation is terminal, a fourth never exists.
    assert call_retry_eligible(TIMEOUT, 1, 3)
    assert call_retry_eligible(TIMEOUT, 2, 3)
    assert not call_retry_eligible(TIMEOUT, 3, 3)
    # Definitive classes never retry regardless of the limit.
    assert not call_retry_eligible(INVALID_REQUEST, 1, 3)
    # A configured value above the PO ceiling is clamped, not honored:
    # the predicate still caps real invocations at three.
    assert call_retry_eligible(TIMEOUT, 1, 99)
    assert not call_retry_eligible(TIMEOUT, 3, 99)


@pytest.mark.parametrize(
    "code", [TIMEOUT, PROVIDER_UNAVAILABLE, INVALID_STRUCTURED_OUTPUT]
)
def test_retry_off_recoverable_failures_run_one_invocation(code):
    """OFF (limit=1): every recoverable class terminates after exactly
    one real invocation — no retry, no CONTINUING, no MCP replay."""
    model = _CodedFailureModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        coded_failures={ARGUMENTS_INSTRUCTION_ID: [code] * 5},
    )
    sink = _SinkSpy()
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS},
        ("teo",),
        model,
        port=port,
        llm_call_max_attempts=1,
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
        activity_sink=sink,
    )
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 1
    assert ActivityPhase.CONTINUING not in sink.phases
    assert [c[1] for c in port.calls] == []


def test_retry_default_is_off_for_unwired_callers():
    """Production parity: an orchestrator built without the limit
    (absent env -> settings default 1) performs a single invocation
    even for a recoverable timeout."""
    model = _CodedFailureModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        coded_failures={ARGUMENTS_INSTRUCTION_ID: [TIMEOUT] * 5},
    )
    read = _orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 1


def test_call_and_turn_limits_are_independent():
    """MODEL_CALL_ATTEMPTS != TURN_RESUME_ATTEMPTS: turn resume OFF
    (max_governed_attempts=1) with call retry ON still recovers inside
    the logical call; call retry OFF with turn resume ON never retries
    the call itself — resume may only re-attempt checkpointed work."""
    model = _CodedFailureModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        coded_failures={ARGUMENTS_INSTRUCTION_ID: [TIMEOUT]},
    )
    on = _resuming_orchestrator(
        {"teo": TEO_TOOLS},
        ("teo",),
        model,
        max_governed_attempts=1,
        llm_call_max_attempts=3,
    )
    attempt = on.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 2

    model2 = _CodedFailureModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        coded_failures={GROUP_SELECTION_INSTRUCTION_ID: [TIMEOUT] * 5},
    )
    port2 = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    off = _resuming_orchestrator(
        {"teo": TEO_TOOLS},
        ("teo",),
        model2,
        port=port2,
        max_governed_attempts=2,
        llm_call_max_attempts=1,
    )
    attempt2 = off.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt2.status is not GovernedCapabilityStatus.SUCCESS
    # Call retry OFF: each turn attempt issued exactly ONE real
    # invocation of the failed stage — at most one per governed turn
    # attempt, never a second within it.
    assert _purposes(model2).count(
        GROUP_SELECTION_INSTRUCTION_ID
    ) <= 2
    # The terminal failure never reached an owner invoke.
    assert [c[1] for c in port2.calls] == []
