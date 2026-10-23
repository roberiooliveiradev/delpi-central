"""DELIA-C3-GOVERNED-STAGE-RESUME-INDEPENDENT-VERIFICATION-01 (CP5).

Independent verification of the CP4 governed stage resume — gates
R1-R4 of the coordination review (doc 91 §6). Reproduces only
defects that can be proven deterministically; everything else is
classified honestly.

R1 — cached outcome is evidence, never authority:
- a PARTIAL/incomplete outcome is not checkpointed: a resumed attempt
  re-invokes the same non-mutating call (a fresh legitimate read);
- a capability removed from the live surface blocks replay;
- a surface-level authorization failure between attempts is terminal;
- a schema change re-validates the replayed arguments against the
  FRESH contract before any invoke.

R2 — the 60s budget anchors at the interaction's clock start:
- time consumed between TurnDeadline.start (execute) and attempt()
  must count against the approved 60s total — the second attempt is
  granted min(30s, remaining-from-interaction-start), never more.

R3 — cancellation inside an attempt:
- a disconnect observed mid-attempt stops the NEXT real operation:
  no new model call, no new provider call after cancellation.
- a ContextVar checkpoint never leaks between interactions.
"""

from __future__ import annotations

import json
import threading
import time

import pytest

from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
    _RESUME_STATE,
)
from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.interaction.activity import (
    ActivityEventSink,
    ActivityPhase,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    InteractiveTurnRequest,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.specialist_interop.contracts import (
    RemoteToolDescriptor,
    RemoteToolOutcome,
)
from app.application.specialist_interop.errors import (
    MCP_AUTHORIZATION_DENIED,
)
from app.create_app import create_app
from tests.test_execution_ceiling_turn_budget import (
    TEST_MODEL_REF,
    VISTA_TOOLS,
    _StageModel,
)
from tests.test_governed_stage_resume import (
    _ClockPort,
    _FlakyStageModel,
    _purposes,
    _resuming_orchestrator,
)
from tests.test_specialist_capability_orchestration import (
    FakePort,
    TEO_TOOLS,
    _interop,
    _select,
)
from tests.test_activity_streaming import (
    PATH,
    NDJSON,
    _context,
    _records,
)


# --- R2: interaction budget anchors at the clock start -------------------


def test_interaction_budget_counts_time_before_the_orchestrator():
    """5s consumed between TurnDeadline.start() (execute) and
    attempt() must reduce the second attempt's window — the 60s cap
    is anchored at the interaction start, not at attempt() entry.

    Doc 103: a lone call timeout recovers inside the logical call —
    the governed turn resume triggers on budget exhaustion, so the
    measured grant moves to the propagating group-selection stage."""
    clock = [1000.0]
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={GROUP_SELECTION_INSTRUCTION_ID: 1},
        clock=clock,
        advance_on_failure=26.0,
    )
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS},
        ("teo",),
        model,
        model_stage_timeout_seconds=40.0,
    )
    deadline = TurnDeadline.start(30.0, clock=lambda: clock[0])
    # 5s of interaction work happens before the orchestrator runs:
    clock[0] += 5.0
    read.attempt(
        "resumo dos indicadores",
        turn_deadline=deadline,
    )
    group_requests = [
        r
        for r in model.requests
        if r.task_purpose_id == GROUP_SELECTION_INSTRUCTION_ID
    ]
    assert len(group_requests) == 2
    # Attempt 1 granted min(40, 30-5)=25s — the turn deadline rules.
    assert group_requests[0].timeout_seconds <= 25.5
    # Attempt 2 must NOT get a full 30s: only 60-5-26=29s remain of
    # the approved interaction budget. If the cap were anchored at
    # attempt() entry it would receive 30s — that is the defect.
    assert group_requests[1].timeout_seconds <= 29.5


def test_no_fourth_invocation_ever():
    """Doc 103: three real invocations per logical call is a hard cap
    — four consecutive timeouts still produce exactly three calls, and
    no turn resume may silently create a forbidden fourth."""
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 4},
    )
    read = _resuming_orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT
    assert attempt.error_code == "model_timeout"
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 3


def test_successful_first_attempt_never_retries():
    model = _StageModel(
        proposals=_select("teo", "analyze", {"view": "summary"})
    )
    read = _resuming_orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    purposes = _purposes(model)
    for purpose in set(purposes):
        assert purposes.count(purpose) == 1


# --- R1: checkpoint is evidence, never authority -------------------------


def test_partial_outcome_is_refetched_not_replayed():
    """A READ that returned an incomplete/partial result is NOT a
    verifiable checkpoint: the resumed attempt must re-invoke the
    same non-mutating call instead of freezing degraded evidence."""
    clock = [1000.0]
    port = _ClockPort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "list_playlists": RemoteToolOutcome(
                content_text=None,
                structured={"records": [{"id": "p1"}]},
                is_complete=False,
            )
        },
        clock=clock,
        advance=35.0,
    )
    model = _StageModel(proposals=_select("vista", "list_playlists"))
    read = _resuming_orchestrator(
        {"vista": VISTA_TOOLS}, ("vista",), model, port=port
    )
    read.attempt(
        "liste minhas programações",
        turn_deadline=TurnDeadline.start(30.0, clock=lambda: clock[0]),
    )
    # The partial outcome is not checkpointable — attempt 2 re-reads:
    assert [c[1] for c in port.calls].count("list_playlists") == 2


def test_schema_change_between_attempts_revalidates_arguments():
    """The owner contract changed between attempts: the replayed
    arguments are re-validated against the FRESH schema — never
    applied to a capability whose contract no longer matches."""

    flipped = RemoteToolDescriptor(
        remote_name="analyze",
        operation_class="READ",
        input_schema={
            "type": "object",
            "properties": {"view": {"type": "string"}},
            "required": ["record_id"],
        },
    )
    other_tools = tuple(
        tool for tool in TEO_TOOLS if tool.remote_name != "analyze"
    )

    class _SchemaFlipPort(FakePort):
        def list_remote_tools(self, specialist, *, timeout_seconds):
            self.list_calls.append(specialist.specialist_id)
            if len(self.list_calls) > 1:
                return other_tools + (flipped,)
            return self._tools.get(specialist.specialist_id, ())

    port = _SchemaFlipPort(tools_by_specialist={"teo": TEO_TOOLS})
    clock = [1000.0]
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        # Exhaust the 30s turn deadline inside an early stage — the
        # turn resume (budget exhaustion) is the governed path under
        # doc 103; a lone call timeout now recovers inside the call.
        failures={GROUP_SELECTION_INSTRUCTION_ID: 1},
        clock=clock,
        advance_on_failure=29.0,
    )
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model, port=port
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0, clock=lambda: clock[0]),
    )
    # Fresh validation must refuse the stale arguments — a terminal
    # that is not a silent SUCCESS over an incompatible contract.
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS
    # No invocation happened on a contract that no longer matches.
    assert [c[1] for c in port.calls].count("analyze") == 0


def test_surface_authorization_failure_between_attempts_is_terminal():
    """A surface-level authorization failure on the fresh listing
    stops the resume: the cached proposal/outcome authorizes nothing
    and the interaction ends honestly."""

    class _RevokedSurfacePort(FakePort):
        def list_remote_tools(self, specialist, *, timeout_seconds):
            self.list_calls.append(specialist.specialist_id)
            if len(self.list_calls) > 1:
                raise CapabilityProviderError(
                    MCP_AUTHORIZATION_DENIED, "delegated grant revoked"
                )
            return self._tools.get(specialist.specialist_id, ())

    port = _RevokedSurfacePort(tools_by_specialist={"teo": TEO_TOOLS})
    clock = [1000.0]
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        # Budget exhaustion at the propagating group stage triggers
        # the governed resume under doc 103; the revoked surface must
        # then stop the second attempt's fresh discovery.
        failures={GROUP_SELECTION_INSTRUCTION_ID: 1},
        clock=clock,
        advance_on_failure=29.0,
    )
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model, port=port
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0, clock=lambda: clock[0]),
    )
    assert attempt.status is not GovernedCapabilityStatus.SUCCESS
    assert [c[1] for c in port.calls] == []


# --- R3: cancellation inside an attempt ----------------------------------


def test_cancel_observed_inside_second_attempt_starts_no_new_model_call():
    """Disconnect lands DURING attempt 2: the next model stage must
    not start a new invocation — cancellation observed mid-attempt
    stops new work, not just new attempts."""

    class _DisconnectPort(FakePort):
        def __init__(self, *args, flag=None, **kwargs):
            super().__init__(*args, **kwargs)
            self._flag = flag

        def list_remote_tools(self, specialist, *, timeout_seconds):
            self.list_calls.append(specialist.specialist_id)
            if self._flag is not None and len(self.list_calls) > 1:
                # The client disconnects while attempt 2 refreshes the
                # live surface — before its first model call.
                self._flag["v"] = True
            return self._tools.get(specialist.specialist_id, ())

    flag = {"v": False}
    port = _DisconnectPort(
        tools_by_specialist={"teo": TEO_TOOLS}, flag=flag
    )
    clock = [1000.0]
    model = _FlakyStageModel(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={GROUP_SELECTION_INSTRUCTION_ID: 1},
        clock=clock,
        advance_on_failure=29.0,
    )
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model, port=port
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0, clock=lambda: clock[0]),
        cancel_check=lambda: flag["v"],
    )
    assert flag["v"] is True
    # Attempt 2 never started a new model call after the observed
    # cancellation — the only requests are attempt 1's admission and
    # its failed group-selection call:
    assert len(model.requests) == 2
    assert _purposes(model).count(ARGUMENTS_INSTRUCTION_ID) == 0
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT


def test_cancel_before_invoke_blocks_the_provider_call():
    """Disconnect lands after the resumed arguments stage but before
    the provider invoke: the read is never issued."""

    class _CancelOnSecondArgs(_FlakyStageModel):
        def __init__(self, *args, flag=None, **kwargs):
            super().__init__(*args, **kwargs)
            self._flag = flag

        def invoke(self, request):
            result = super().invoke(request)
            if (
                request.task_purpose_id == ARGUMENTS_INSTRUCTION_ID
                and self._flag is not None
            ):
                # The client disconnected while attempt 2's arguments
                # stage completed — before the provider invoke.
                self._flag["v"] = True
            return result

    flag = {"v": False}
    port = FakePort(tools_by_specialist={"teo": TEO_TOOLS})
    model = _CancelOnSecondArgs(
        proposals=_select("teo", "analyze", {"view": "summary"}),
        failures={ARGUMENTS_INSTRUCTION_ID: 1},
        flag=flag,
    )
    read = _resuming_orchestrator(
        {"teo": TEO_TOOLS}, ("teo",), model, port=port
    )
    attempt = read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
        cancel_check=lambda: flag["v"],
    )
    assert flag["v"] is True
    assert [c[1] for c in port.calls] == []
    assert attempt.status is GovernedCapabilityStatus.PROCESSING_TIMEOUT


def test_checkpoint_state_never_leaks_between_interactions():
    """The request-scoped checkpoint is bound per attempt() call and
    reset on return — a second interaction on the SAME orchestrator
    sees no stale proposals."""
    model = _StageModel(
        proposals=_select("teo", "analyze", {"view": "summary"})
    )
    read = _resuming_orchestrator({"teo": TEO_TOOLS}, ("teo",), model)
    read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    assert _RESUME_STATE.get() is None
    calls_before = len(model.requests)
    read.attempt(
        "resumo dos indicadores",
        turn_deadline=TurnDeadline.start(30.0),
    )
    # The second interaction ran its own stages — nothing replayed
    # from the first interaction's checkpoint:
    assert len(model.requests) > calls_before


# --- R3: stream-level disconnect (real route, fake handler) --------------


class _BlockingTurnHandler:
    """Emits one observed event, then waits inside execute() until the
    transport's cancel_check fires — simulating in-flight work at the
    moment the client disconnects."""

    def __init__(self, event=None):
        self.observed_cancel: bool | None = None
        self.returned = threading.Event()
        self._event = event or threading.Event()

    def execute(
        self, request, *, activity_channel=None, cancel_check=None
    ):
        sink = ActivityEventSink(
            activity_channel, session_id="s1", turn_id="t1"
        )
        sink.emit(phase=ActivityPhase.REQUEST_RECEIVED)
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if cancel_check is not None and cancel_check():
                self.observed_cancel = True
                break
            if self._event.is_set():
                break
            time.sleep(0.01)
        else:
            self.observed_cancel = False
        self.returned.set()
        from app.application.interaction.contracts import (
            InteractiveTurnResult,
        )
        from app.domain.evidence.model import EpistemicClass

        return InteractiveTurnResult(
            session_id="s1",
            user_turn_id="t0",
            result_turn_id="t1",
            content="done",
            epistemic_class=EpistemicClass.OBSERVATION,
            limitations=(),
            generated_at="2026-01-01T00:00:00+00:00",
            model_invocation_id=None,
        )


class _PlatformAccess:
    def __init__(self, context=None):
        self._context = context or _context()

    def resolve(self, bearer_token: str):
        return self._context


def _stream_client(handler):
    app = create_app(
        testing=True,
        platform_access_provider=_PlatformAccess(),
        interaction_turn_handler=handler,
    )
    return app.test_client()


def test_stream_disconnect_signals_cancel_and_worker_finishes_bounded():
    """Client closes the NDJSON stream mid-turn: GeneratorExit sets
    the disconnect event, the handler observes cancel_check(), and
    the worker finishes bounded — result discarded, terminal once."""
    handler = _BlockingTurnHandler()
    client = _stream_client(handler)
    response = client.post(
        PATH,
        json={"input": "oi"},
        headers={"Authorization": "Bearer t", "Accept": NDJSON},
        buffered=False,
    )
    # First event arrives — the stream is alive.
    line = next(response.response)
    assert b"REQUEST_RECEIVED" in line
    # Client disconnects while the handler is in flight.
    response.close()
    # The worker finishes bounded — never killed, never re-executed:
    assert handler.returned.wait(timeout=5.0)
    assert handler.observed_cancel is True


def test_continuing_phase_is_delivered_on_the_live_stream():
    """CONTINUING is a wire-legal observed phase: the client sees it
    while the stream is alive, before the authoritative terminal."""

    class _ContinuingHandler(_BlockingTurnHandler):
        def execute(
            self, request, *, activity_channel=None, cancel_check=None
        ):
            sink = ActivityEventSink(
                activity_channel, session_id="s1", turn_id="t1"
            )
            sink.emit(phase=ActivityPhase.REQUEST_RECEIVED)
            sink.emit(phase=ActivityPhase.CONTINUING)
            self._event.set()
            return super().execute(
                request,
                activity_channel=activity_channel,
                cancel_check=cancel_check,
            )

    handler = _ContinuingHandler()
    client = _stream_client(handler)
    response = client.post(
        PATH,
        json={"input": "oi"},
        headers={"Authorization": "Bearer t", "Accept": NDJSON},
        buffered=False,
    )
    phases = [
        record["phase"]
        for record in _records(
            line.decode() for line in response.response
        )
        if record.get("type") == "activity_event"
    ]
    assert phases[0] == "REQUEST_RECEIVED"
    assert "CONTINUING" in phases
