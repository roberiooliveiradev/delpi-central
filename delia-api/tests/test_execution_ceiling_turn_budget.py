"""C3-INTELLIGENCE-LOOP-03R2A — execution ceiling HTTP contract +
hard model/turn deadlines.

STOP-THE-LINE coverage for the production regression:

- HTTP boundary accepts only the reduction ceiling "prepare"
- application-layer validation is fail-closed for internally built
  requests (never rely on the Flask boundary alone)
- model invocation enforces a TOTAL wall-clock deadline — a trickling
  server cannot keep the call alive
- one shared turn budget clamps every governed stage; a model-stage
  timeout terminates as SOURCE_UNAVAILABLE and never degrades into a
  general-model answer
- candidate disambiguation/argument model calls carry the same safe
  timing + correlation telemetry; synthesis fallback logs a bounded
  reason code
"""

from __future__ import annotations

import json
import logging
import socket
import threading
import time

import pytest

from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    InteractiveTurnRequest,
    InteractiveTurnResult,
)
from app.application.interaction.errors import (
    INVALID_REQUEST,
    InteractionError,
)
from app.application.interaction.handle_interactive_turn import (
    DELPI_SOURCE_UNAVAILABLE_MESSAGE,
    HandleInteractiveConversationTurn,
)
from app.application.interaction.turn_budget import (
    TurnBudgetExhausted,
    TurnDeadline,
)
from app.application.capability_provision.mcp_provider import (
    McpCapabilityProvider,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CANDIDATE_ARGUMENTS_INSTRUCTION_ID,
    CANDIDATE_SELECTION_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GOAL_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
    SYNTHESIS_INSTRUCTION_ID,
    OperationalCapabilityOrchestrator,
)
from app.application.model_invocation.contracts import (
    ModelInvocationRequest,
    ProviderInvocationPayload,
)
from app.application.model_invocation.errors import (
    TIMEOUT,
    ModelInvocationError,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.application.specialist_interop.contracts import (
    DEFAULT_INVOCATION_TIMEOUT_SECONDS,
    RemoteToolDescriptor,
    RemoteToolOutcome,
    SpecialistInvocationRequest,
)
from app.application.specialist_interop.errors import (
    MCP_TIMEOUT,
    SpecialistInteropError,
)
from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.create_app import create_app
from app.domain.evidence.model import EpistemicClass, ModelRef
from app.domain.interaction.model import GroundingStatus
from app.domain.model_invocation.model import (
    InvocationFinishStatus,
    ModelInvocationId,
    ProviderExposureClass,
)
from app.infrastructure.model_invocation.openai_compatible_adapter import (
    OpenAICompatibleModelInvocationAdapter,
)
from tests.test_specialist_capability_orchestration import (
    CANDIDATE_EXECUTOR_SCHEMA,
    COMMIT_VERIFIED,
    DIRECT_PROPOSAL,
    MULTI_CANDIDATE_RESULT,
    READY_PROPOSAL,
    VISTA_OPS_CATALOG,
    VISTA_TOOLS,
    FakePort,
    _confirmation,
    _interop,
    _read,
    _select,
    _vista_ops_prepare,
)


PATH = "/interaction/turns"
TEST_MODEL_REF = ModelRef(
    model_id="test-model", version="1", owner_ref="DELPI"
)

DAVI_CANDIDATE_TOOLS = (
    RemoteToolDescriptor(
        remote_name="discover_delpi_information",
        operation_class="DISCOVERY",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    ),
    RemoteToolDescriptor(
        remote_name="execute_delpi_information",
        operation_class="READ",
        input_schema=CANDIDATE_EXECUTOR_SCHEMA,
    ),
)

TEO_ARG_TOOLS = (
    RemoteToolDescriptor(
        remote_name="get_catalog", operation_class="DISCOVERY"
    ),
    RemoteToolDescriptor(
        remote_name="analyze",
        operation_class="READ",
        input_schema={
            "type": "object",
            "properties": {"view": {"type": "string"}},
        },
    ),
)

_STAGE_DEFAULTS = {
    GOAL_INSTRUCTION_ID: {"goal_class": "read"},
    GROUP_SELECTION_INSTRUCTION_ID: {"applicable": True},
    NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
}


class _StageModel:
    """Proposal model that answers valid payloads per purpose — or
    raises ModelInvocationError(TIMEOUT) for one designated stage."""

    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(
        self,
        proposals: dict | None = None,
        timeout_purposes: frozenset[str] = frozenset(),
    ) -> None:
        self._proposals = {**_STAGE_DEFAULTS, **(proposals or {})}
        self._timeout_purposes = set(timeout_purposes)
        self.requests: list[ModelInvocationRequest] = []

    def invoke(self, request: ModelInvocationRequest):
        self.requests.append(request)
        if request.task_purpose_id in self._timeout_purposes:
            raise ModelInvocationError(TIMEOUT, "stage timed out")
        resolved = self._proposals.get(request.task_purpose_id)
        return ProviderInvocationPayload(
            structured_output=(
                resolved if isinstance(resolved, dict) else {}
            ),
            generated_at="2026-01-01T00:00:00+00:00",
        )


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="u1",
        name="User",
        email="u@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


class _AccessProvider:
    def resolve(self, bearer_token: str):
        return _context()


def _client(handler=None):
    app = create_app(
        testing=True,
        platform_access_provider=_AccessProvider(),
        interaction_turn_handler=handler,
    )
    return app.test_client()


def _orchestrator(
    tools_by_specialist,
    specialist_ids,
    model,
    *,
    outcomes=None,
    port=None,
    turn_budget_seconds=80.0,
) -> OperationalCapabilityOrchestrator:
    port = port or FakePort(
        tools_by_specialist=tools_by_specialist, outcomes=outcomes
    )
    return OperationalCapabilityOrchestrator(
        [McpCapabilityProvider(_interop(port), specialist_ids)],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
        turn_budget_seconds=turn_budget_seconds,
    )


# --- HTTP execution ceiling -------------------------------------------------


class _SpyHandler:
    """Captures the application request; returns a minimal result."""

    def __init__(self) -> None:
        self.requests: list[InteractiveTurnRequest] = []

    def execute(self, request: InteractiveTurnRequest):
        self.requests.append(request)
        return InteractiveTurnResult(
            session_id="s1",
            user_turn_id="u1",
            result_turn_id="r1",
            content="ok",
            epistemic_class=EpistemicClass.HYPOTHESIS,
            limitations=(),
            generated_at="2026-01-01T00:00:00+00:00",
            model_invocation_id=None,
            grounding_status=GroundingStatus.NON_GROUNDED,
        )


def test_http_absent_ceiling_is_legacy_accepted():
    spy = _SpyHandler()
    response = _client(handler=spy).post(
        PATH,
        json={"input": "olá"},
        headers={"Authorization": "Bearer t"},
    )
    assert response.status_code == 200
    assert spy.requests[0].max_execution_stage is None


def test_http_prepare_ceiling_reaches_application_contract():
    spy = _SpyHandler()
    response = _client(handler=spy).post(
        PATH,
        json={"input": "olá", "max_execution_stage": "prepare"},
        headers={"Authorization": "Bearer t"},
    )
    assert response.status_code == 200
    assert spy.requests[0].max_execution_stage == "prepare"


def test_http_prepare_ceiling_null_is_legacy_accepted():
    spy = _SpyHandler()
    response = _client(handler=spy).post(
        PATH,
        json={"input": "olá", "max_execution_stage": None},
        headers={"Authorization": "Bearer t"},
    )
    assert response.status_code == 200
    assert spy.requests[0].max_execution_stage is None


@pytest.mark.parametrize(
    "value",
    ["act", "execute", "direct", "ACT", "preparee", "PREPARE", "", 5, True],
)
def test_http_escalation_ceiling_fails_closed_400(value):
    spy = _SpyHandler()
    response = _client(handler=spy).post(
        PATH,
        json={"input": "olá", "max_execution_stage": value},
        headers={"Authorization": "Bearer t"},
    )
    assert response.status_code == 400
    assert response.get_json()["code"] == INVALID_REQUEST
    assert spy.requests == []


@pytest.mark.parametrize("value", [{"stage": "prepare"}, ["prepare"]])
def test_http_non_scalar_ceiling_fails_closed_400(value):
    response = _client(handler=_SpyHandler()).post(
        PATH,
        json={"input": "olá", "max_execution_stage": value},
        headers={"Authorization": "Bearer t"},
    )
    assert response.status_code == 400
    assert response.get_json()["code"] == INVALID_REQUEST


# --- Application-layer ceiling defense --------------------------------------


def _bare_handler() -> HandleInteractiveConversationTurn:
    return HandleInteractiveConversationTurn(
        InvokeModel(
            _StageModel(
                proposals={"delia.interaction.turn": {"answer": "ok"}}
            ),
        )
    )


@pytest.mark.parametrize(
    "value",
    ["act", "execute", "direct", "ACT", "", 5, True, {"x": 1}, ["prepare"]],
)
def test_application_invalid_ceiling_fails_closed(value):
    handler = _bare_handler()
    with pytest.raises(InteractionError) as exc:
        handler.execute(
            InteractiveTurnRequest(
                access_context=_context(),
                input_text="olá",
                max_execution_stage=value,
            )
        )
    assert exc.value.code == INVALID_REQUEST


def test_application_none_and_prepare_ceiling_accepted():
    handler = _bare_handler()
    for value in (None, "prepare"):
        result = handler.execute(
            InteractiveTurnRequest(
                access_context=_context(),
                input_text="olá",
                max_execution_stage=value,
            )
        )
        assert result.session_id


# --- Turn deadline + terminal model timeouts --------------------------------


def test_turn_budget_exhausted_is_terminal_source_unavailable():
    """An exhausted turn budget terminates deterministically — the
    governed attempt never reaches a general answer."""
    orchestrator = _orchestrator(
        {"vista": VISTA_TOOLS},
        ("vista",),
        _StageModel(proposals={}),
        turn_budget_seconds=0.0,
    )
    attempt = orchestrator.attempt("Liste meus painéis")
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == "turn_budget_exhausted"


def test_select_group_timeout_is_terminal_not_general_fallback():
    """select_group model TIMEOUT -> SOURCE_UNAVAILABLE(model_timeout).

    Two groups force the group-selection model call; the timeout is a
    governed orchestration failure — never a NOT_APPLICABLE that would
    degrade into a general-model answer.
    """
    orchestrator = _orchestrator(
        {"vista": VISTA_TOOLS, "teo": TEO_ARG_TOOLS},
        ("vista", "teo"),
        _StageModel(timeout_purposes=frozenset({GROUP_SELECTION_INSTRUCTION_ID})),
    )
    attempt = orchestrator.attempt("Liste meus painéis")
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == "model_timeout"


def test_select_capability_timeout_is_terminal():
    orchestrator = _orchestrator(
        {"vista": VISTA_TOOLS},
        ("vista",),
        _StageModel(
            timeout_purposes=frozenset({CAPABILITY_SELECTION_INSTRUCTION_ID})
        ),
    )
    attempt = orchestrator.attempt("Liste meus painéis")
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == "model_timeout"


def test_argument_timeout_is_terminal():
    """Argument projection TIMEOUT -> deterministic governed failure."""
    orchestrator = _orchestrator(
        {"teo": TEO_ARG_TOOLS},
        ("teo",),
        _StageModel(
            proposals={
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "analyze",
                },
            },
            timeout_purposes=frozenset({ARGUMENTS_INSTRUCTION_ID}),
        ),
    )
    attempt = orchestrator.attempt("Analise o painel")
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == "model_timeout"


def test_operational_timeout_never_calls_general_model():
    """Handler-level: a governed-path model timeout is answered by the
    deterministic terminal surface — the general model port is never
    invoked for the same turn."""
    general_port = _StageModel(proposals={})
    orchestrator = _orchestrator(
        {"vista": VISTA_TOOLS},
        ("vista",),
        _StageModel(
            timeout_purposes=frozenset({CAPABILITY_SELECTION_INSTRUCTION_ID})
        ),
    )
    handler = HandleInteractiveConversationTurn(
        InvokeModel(general_port),
        capability_orchestration=orchestrator,
    )
    result = handler.execute(
        InteractiveTurnRequest(
            access_context=_context(), input_text="Liste meus painéis"
        )
    )
    assert general_port.requests == []
    assert result.content == DELPI_SOURCE_UNAVAILABLE_MESSAGE
    assert result.epistemic_class is EpistemicClass.HYPOTHESIS
    assert result.grounding_status is GroundingStatus.NON_GROUNDED
    assert "delpi_source_unverified" in result.limitations


def test_general_path_receives_clamped_budget():
    """The general conversational call is clamped to the remaining
    turn budget — never a fresh full timeout after orchestration."""
    orchestrator = _orchestrator(
        {},
        ("vista",),
        _StageModel(proposals={}),
    )
    general_port = _StageModel(
        proposals={"delia.interaction.turn": {"answer": "ok"}}
    )
    handler = HandleInteractiveConversationTurn(
        InvokeModel(general_port),
        capability_orchestration=orchestrator,
        turn_budget_seconds=42.0,
    )
    result = handler.execute(
        InteractiveTurnRequest(
            access_context=_context(), input_text="olá"
        )
    )
    assert result.content == "ok"
    assert general_port.requests
    assert (
        general_port.requests[-1].timeout_seconds <= 42.0
    )


def test_exhausted_budget_blocks_general_model_call():
    handler = HandleInteractiveConversationTurn(
        InvokeModel(_StageModel(proposals={})),
        turn_budget_seconds=0.0,
    )
    with pytest.raises(InteractionError) as exc:
        handler.execute(
            InteractiveTurnRequest(
                access_context=_context(), input_text="olá"
            )
        )
    assert exc.value.code == "model_timeout"


# --- Write ceiling regression (zero ACT under prepare) -----------------------


def test_direct_policy_prepare_ceiling_zero_act_calls():
    """R2A gate F: owner-declared direct execution + prepare ceiling
    reaches the orchestration boundary — PREPARE runs, ACT calls = 0."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "get_catalog": VISTA_OPS_CATALOG,
            "prepare_change": DIRECT_PROPOSAL,
            "commit_proposal": COMMIT_VERIFIED,
        },
    )
    read = _vista_ops_prepare(port, [{"op": "add_blank_slide"}])
    attempt = read.attempt(
        "crie um slide",
        actor_user_id="u1",
        session_id="s1",
        max_execution_stage="prepare",
    )
    assert attempt.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    assert "commit_proposal" not in [c[1] for c in port.calls]


def test_confirmation_under_prepare_ceiling_never_acts():
    """R2A gate G: a structured confirmation under the ceiling is
    refused — the ceiling binds the whole turn, pending write
    included. ACT calls = 0."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "get_catalog": VISTA_OPS_CATALOG,
            "prepare_change": READY_PROPOSAL,
            "commit_proposal": COMMIT_VERIFIED,
        },
    )
    read = _vista_ops_prepare(port, [{"op": "delete_slide"}])
    pending = read.attempt(
        "exclua este slide",
        actor_user_id="u1",
        session_id="s1",
        max_execution_stage="prepare",
    )
    assert pending.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    result = read.attempt(
        "",
        actor_user_id="u1",
        confirmation=_confirmation(pending),
        max_execution_stage="prepare",
    )
    assert result.status is GovernedCapabilityStatus.WRITE_REJECTED
    assert result.error_code == "execution_ceiling"
    assert "commit_proposal" not in [c[1] for c in port.calls]


# --- Hard wall-clock model deadline ------------------------------------------


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _serve_forever(handler) -> tuple[int, threading.Event]:
    """Tiny raw-socket HTTP server on a background thread."""
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    done = threading.Event()

    def run():
        try:
            conn, _ = listener.accept()
            conn.settimeout(5.0)
            handler(conn)
        except OSError:
            pass
        finally:
            done.set()
            listener.close()

    threading.Thread(target=run, daemon=True).start()
    return listener.getsockname()[1], done


def _model_request(timeout: float) -> ModelInvocationRequest:
    from app.application.interaction.instruction import (
        interaction_instruction_lineage,
    )
    from app.domain.model_invocation.model import (
        InstructionLineage,
    )

    return ModelInvocationRequest(
        invocation_id=ModelInvocationId("inv-deadline"),
        model_ref=TEST_MODEL_REF,
        input_text="olá",
        task_purpose_id="delia.interaction.turn",
        output_schema_id="delia.interaction.turn",
        output_schema_version="1",
        expected_fields=("answer",),
        instruction_lineage=interaction_instruction_lineage(),
        timeout_seconds=timeout,
        instruction_content="You are DÉLIA.",
    )


def test_trickle_server_never_outlives_wall_clock_deadline():
    """A server that accepts the request and emits bytes slowly —
    enough that a per-read timeout never fires — must still terminate
    at the total deadline."""
    started_serving = threading.Event()

    def trickle(conn):
        try:
            conn.recv(65536)
            conn.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: 1000000\r\n\r\n"
            )
            started_serving.set()
            while True:
                conn.sendall(b'"')
                time.sleep(0.05)
        except OSError:
            pass
        finally:
            conn.close()

    port, done = _serve_forever(trickle)
    adapter = OpenAICompatibleModelInvocationAdapter(
        base_url=f"http://127.0.0.1:{port}",
        api_key="test-key",
        model="vendor/model",
        timeout_seconds=30.0,
    )
    started = time.monotonic()
    with pytest.raises(ModelInvocationError) as exc:
        adapter.invoke(_model_request(timeout=1.0))
    elapsed = time.monotonic() - started
    assert exc.value.code == TIMEOUT
    # The call must end near the requested 1.0s budget — one read
    # slice plus scheduling slack, certainly not the configured 30s.
    assert elapsed < 5.0
    assert started_serving.is_set()
    done.wait(timeout=5.0)


def test_normal_fast_provider_preserves_response_contract():
    """A prompt provider still completes normally — structured output
    and duration metadata preserved through the streaming drain."""

    def fast(conn):
        try:
            conn.recv(65536)
            body = json.dumps(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"answer": "ok"}'
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 3,
                        "completion_tokens": 1,
                    },
                }
            ).encode()
            conn.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: "
                + str(len(body)).encode()
                + b"\r\n\r\n"
                + body
            )
        except OSError:
            pass
        finally:
            conn.close()

    port, done = _serve_forever(fast)
    adapter = OpenAICompatibleModelInvocationAdapter(
        base_url=f"http://127.0.0.1:{port}",
        api_key="test-key",
        model="vendor/model",
        timeout_seconds=30.0,
    )
    result = adapter.invoke(_model_request(timeout=10.0))
    assert result.structured_output["answer"] == "ok"
    assert result.finish_status is InvocationFinishStatus.COMPLETED
    assert result.usage.input_units == 3
    assert isinstance(result.duration_ms, int)
    done.wait(timeout=5.0)


# --- TurnDeadline contract ----------------------------------------------------


class _FakeClock:
    def __init__(self, now: float = 1000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_turn_deadline_remaining_and_exhaustion():
    clock = _FakeClock()
    deadline = TurnDeadline.start(80.0, clock=clock)
    assert deadline.remaining_seconds() == 80.0
    assert not deadline.exhausted()
    clock.advance(79.9)
    assert deadline.remaining_seconds() == pytest.approx(0.1)
    assert not deadline.exhausted()
    clock.advance(0.2)
    assert deadline.exhausted()
    assert deadline.remaining_seconds() == 0.0


def test_turn_deadline_stage_timeout_is_reduction_only():
    clock = _FakeClock()
    deadline = TurnDeadline.start(80.0, clock=clock)
    assert deadline.stage_timeout(10.0) == 10.0
    clock.advance(75.0)
    assert deadline.stage_timeout(10.0) == 5.0
    assert deadline.stage_timeout(3.0) == 3.0


def test_turn_deadline_zero_or_negative_budget_is_exhausted():
    clock = _FakeClock()
    assert TurnDeadline.start(0.0, clock=clock).exhausted()
    assert TurnDeadline.start(-5.0, clock=clock).exhausted()
    assert (
        TurnDeadline.start(-5.0, clock=clock).stage_timeout(10.0) == 0.0
    )


def test_turn_deadline_check_blocks_stage_start_when_exhausted():
    clock = _FakeClock()
    deadline = TurnDeadline.start(1.0, clock=clock)
    deadline.check("model_propose")
    clock.advance(1.1)
    with pytest.raises(TurnBudgetExhausted) as exc:
        deadline.check("model_propose")
    assert exc.value.stage == "model_propose"


# --- Safe model-call observability -------------------------------------------


@pytest.fixture
def app_log_propagation():
    """create_app() (HTTP tests) configures "app" with its own
    handler, propagate=False and WARNING level — caplog only sees
    app.* records while propagation + level are temporarily
    restored."""
    app_logger = logging.getLogger("app")
    previous = (app_logger.propagate, app_logger.level)
    app_logger.propagate = True
    app_logger.setLevel(logging.INFO)
    yield
    app_logger.propagate, app_logger.level = previous


def test_candidate_stages_emit_safe_timing(caplog, app_log_propagation):
    """Candidate disambiguation + candidate argument proposals emit
    the standard stage=model_propose timing schema with correlation —
    and never candidate tokens or argument values."""
    port = FakePort(
        tools_by_specialist={"davi": DAVI_CANDIDATE_TOOLS},
        outcomes={
            "discover_delpi_information": MULTI_CANDIDATE_RESULT
        },
    )
    model = _StageModel(
        proposals={
            CAPABILITY_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "remote_name": "execute_delpi_information",
            },
            ARGUMENTS_INSTRUCTION_ID: {
                # inner args that fail the candidate's own schema —
                # forces the bounded second proposal stage.
                "arguments": {"arguments": {"code": "tubo"}}
            },
            CANDIDATE_SELECTION_INSTRUCTION_ID: {
                "applicable": True,
                "action_id": "search_products",
            },
            CANDIDATE_ARGUMENTS_INSTRUCTION_ID: {
                "arguments": {"description": "tubo"}
            },
        }
    )
    orchestrator = OperationalCapabilityOrchestrator(
        [McpCapabilityProvider(_interop(port), ("davi",))],
        invoke_model=InvokeModel(model),
        model_ref=TEST_MODEL_REF,
    )
    with caplog.at_level(logging.INFO):
        attempt = orchestrator.attempt("busque tubo")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    model_logs = [
        r.message
        for r in caplog.records
        if "stage=model_propose" in r.message
    ]
    purposes = {
        r.message.split("purpose=")[1].split()[0]
        for r in caplog.records
        if "purpose=" in r.message
    }
    assert CANDIDATE_SELECTION_INSTRUCTION_ID in purposes
    assert CANDIDATE_ARGUMENTS_INSTRUCTION_ID in purposes
    assert any("timing_ms=" in m for m in model_logs)
    assert any("correlation_id=" in m for m in model_logs)
    joined = "\n".join(m for m in caplog.messages)
    assert "tok-parents" not in joined
    assert "tok-search" not in joined
    assert "tubo" not in joined


def test_synthesis_fallback_logs_bounded_reason(
    caplog, app_log_propagation
):
    """A rejected synthesis proposal logs exactly one bounded reason
    code — never proposal content."""
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "list_playlists": RemoteToolOutcome(
                content_text="{}",
                structured={
                    "data": {
                        "items": [
                            {"name": "Painel A"},
                            {"name": "Painel B"},
                        ]
                    }
                },
            )
        },
    )
    orchestrator = _orchestrator(
        {"vista": VISTA_TOOLS},
        ("vista",),
        _StageModel(
            proposals={
                CAPABILITY_SELECTION_INSTRUCTION_ID: {
                    "applicable": True,
                    "remote_name": "list_playlists",
                },
                SYNTHESIS_INSTRUCTION_ID: {
                    "items": [
                        {"record_index": 99, "fields": ["name"]}
                    ]
                },
            }
        ),
        port=port,
    )
    with caplog.at_level(logging.INFO):
        attempt = orchestrator.attempt("Liste meus painéis")
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    synth_logs = [
        r.message
        for r in caplog.records
        if "stage=synthesis" in r.message
    ]
    assert any(
        "decision=fallback" in m and "reason=" in m
        for m in synth_logs
    )


# --- R1: end-to-end turn deadline across provider boundaries ------------------
#
# LOOP-03R2A-R1: the review found the deadline was CHECKED before
# provider operations but the remaining budget was never PASSED into
# them. These tests prove the bounded timeout reaches the transport
# seam and that an overrun — whether the provider reports it or
# returns stale success — terminates truthfully as SOURCE_UNAVAILABLE
# with zero general-model fallback.


class _DeadlinePort(FakePort):
    """FakePort that records every ``timeout_seconds`` it receives and
    can consume a shared fake clock per call (seconds advanced per
    call index — the last spec value repeats)."""

    def __init__(
        self,
        *args,
        clock=None,
        list_seconds=0.0,
        call_seconds=0.0,
        real_list_sleep=0.0,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._clock = clock
        self._list_seconds = list_seconds
        self._call_seconds = call_seconds
        self._real_list_sleep = real_list_sleep
        self.list_timeouts: list[float] = []
        self.call_timeouts: list[float] = []

    @staticmethod
    def _consume(spec, index):
        if isinstance(spec, (int, float)):
            return float(spec)
        return float(spec[min(index, len(spec) - 1)])

    def list_remote_tools(self, specialist, *, timeout_seconds):
        self.list_timeouts.append(timeout_seconds)
        if self._real_list_sleep:
            time.sleep(self._real_list_sleep)
        if self._clock is not None:
            self._clock[0] += self._consume(
                self._list_seconds, len(self.list_timeouts) - 1
            )
        return super().list_remote_tools(
            specialist, timeout_seconds=timeout_seconds
        )

    def call_remote_tool(
        self,
        specialist,
        remote_name,
        arguments,
        *,
        correlation_id,
        timeout_seconds,
    ):
        self.call_timeouts.append(timeout_seconds)
        if self._clock is not None:
            self._clock[0] += self._consume(
                self._call_seconds, len(self.call_timeouts) - 1
            )
        return super().call_remote_tool(
            specialist,
            remote_name,
            arguments,
            correlation_id=correlation_id,
            timeout_seconds=timeout_seconds,
        )


def _deadline(clock, budget_seconds):
    return TurnDeadline(
        ends_at=clock[0] + budget_seconds, clock=lambda: clock[0]
    )


def _vista_listing(interop):
    return _read(
        interop,
        specialist_ids=("vista",),
        proposal=_select("vista", "list_playlists", {}),
    )


# A. initial list_groups bounded by the remaining turn budget
def test_r1_initial_surface_list_overrun_is_source_unavailable():
    """A surface consultation that consumes past the turn deadline
    ends SOURCE_UNAVAILABLE — its late result is never projected."""
    clock = [1000.0]
    port = _DeadlinePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        clock=clock,
        list_seconds=200.0,
    )
    read = _vista_listing(_interop(port))
    attempt = read.attempt(
        "liste", turn_deadline=_deadline(clock, 80.0)
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == "turn_budget_exhausted"
    # The stage max (15s) bounded the granted timeout — never the
    # full turn budget — and no invocation was reached.
    assert port.list_timeouts == [
        DEFAULT_INVOCATION_TIMEOUT_SECONDS
    ]
    assert port.calls == []


def test_r1_initial_surface_list_real_overrun_bounded_elapsed():
    """Real-clock variant: a provider that overruns the remaining
    budget cannot stretch the turn — the boundary check terminates
    within budget + tolerance."""
    port = _DeadlinePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        real_list_sleep=0.30,
    )
    read = _vista_listing(_interop(port))
    started = time.monotonic()
    attempt = read.attempt(
        "liste", turn_deadline=TurnDeadline.start(0.10)
    )
    elapsed = time.monotonic() - started
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert elapsed < 1.0
    assert port.calls == []


# B. fresh live re-list (write-path revalidation) bounded
def test_r1_fresh_relist_overrun_is_source_unavailable():
    """The ACT-path fresh re-list shares the same deadline — an
    overrun there fails closed before the commit invocation."""
    clock = [1000.0]
    port = _DeadlinePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "get_catalog": VISTA_OPS_CATALOG,
            "prepare_change": DIRECT_PROPOSAL,
            "commit_proposal": COMMIT_VERIFIED,
        },
        clock=clock,
        # list#1 catalog, list#2+#3 invoke revalidations, list#4
        # fresh re-list before the write decision — the fourth
        # blows the deadline.
        list_seconds=(0.0, 0.0, 0.0, 200.0),
    )
    read = _vista_ops_prepare(port, [{"op": "delete_slide"}])
    attempt = read.attempt(
        "exclua este slide",
        actor_user_id="u1",
        turn_deadline=_deadline(clock, 80.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == "turn_budget_exhausted"
    # Discovery + PREPARE ran inside the budget; the exhausted
    # re-list stops the chain before any commit.
    assert [c[1] for c in port.calls] == [
        "get_catalog",
        "prepare_change",
    ]
    assert "commit_proposal" not in [c[1] for c in port.calls]
    assert all(
        t <= DEFAULT_INVOCATION_TIMEOUT_SECONDS
        for t in port.list_timeouts
    )


# C. provider invoke bounded
def test_r1_invoke_overrun_is_source_unavailable():
    """An invocation outcome that arrives after the turn deadline is
    never processed — post-call boundary check fails truthfully."""
    clock = [1000.0]
    port = _DeadlinePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={"get_catalog": VISTA_OPS_CATALOG},
        clock=clock,
        call_seconds=200.0,
    )
    read = _vista_ops_prepare(port, [{"op": "add_blank_slide"}])
    attempt = read.attempt(
        "crie um slide",
        actor_user_id="u1",
        turn_deadline=_deadline(clock, 80.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == "turn_budget_exhausted"
    assert [c[1] for c in port.calls] == ["get_catalog"]
    assert all(
        0 < t <= DEFAULT_INVOCATION_TIMEOUT_SECONDS
        for t in port.call_timeouts
    )


# D. candidate/discovery chain — next stage receives only the remainder
def test_r1_next_stage_receives_only_remaining_budget():
    """After the surface list consumed most of the budget, the next
    provider stages receive the remainder — never the configured
    stage max."""
    clock = [1000.0]
    port = _DeadlinePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        clock=clock,
        list_seconds=79.5,
    )
    read = _vista_listing(_interop(port))
    attempt = read.attempt(
        "liste", turn_deadline=_deadline(clock, 80.0)
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    # list#1 got the stage max; list#2 (invoke revalidation) got only
    # the 0.5s remainder — not the full provider timeout again.
    assert port.list_timeouts[0] == DEFAULT_INVOCATION_TIMEOUT_SECONDS
    assert 0 < port.list_timeouts[1] <= 0.5 + 0.05
    assert all(t > 0 for t in port.call_timeouts)


# E. PREPARE with exhausted / near-exhausted budget — no ACT
def test_r1_exhausted_budget_at_turn_start_fails_closed():
    clock = [1000.0]
    port = _DeadlinePort(
        tools_by_specialist={"vista": VISTA_TOOLS}, clock=clock
    )
    read = _vista_listing(_interop(port))
    deadline = _deadline(clock, 80.0)
    clock[0] += 200.0
    attempt = read.attempt("liste", turn_deadline=deadline)
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert attempt.error_code == "turn_budget_exhausted"
    # No provider stage may start once the deadline passed.
    assert port.list_calls == []
    assert port.calls == []


def test_r1_budget_exhausted_before_prepare_no_write():
    """Budget consumed during discovery: the prepare path never
    reaches any write capability and ends truthfully."""
    clock = [1000.0]
    port = _DeadlinePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={"get_catalog": VISTA_OPS_CATALOG},
        clock=clock,
        # Discovery consumes past the deadline — the post-invoke
        # boundary check stops the chain before PREPARE.
        call_seconds=80.5,
    )
    read = _vista_ops_prepare(port, [{"op": "delete_slide"}])
    attempt = read.attempt(
        "exclua este slide",
        actor_user_id="u1",
        turn_deadline=_deadline(clock, 80.0),
    )
    assert attempt.status is GovernedCapabilityStatus.SOURCE_UNAVAILABLE
    assert [c[1] for c in port.calls] == ["get_catalog"]
    assert "commit_proposal" not in [c[1] for c in port.calls]


# F. confirmation continuation under prepare ceiling — zero ACT
def test_r1_confirmation_under_prepare_ceiling_zero_act():
    port = FakePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        outcomes={
            "get_catalog": VISTA_OPS_CATALOG,
            "prepare_change": READY_PROPOSAL,
            "commit_proposal": COMMIT_VERIFIED,
        },
    )
    read = _vista_ops_prepare(port, [{"op": "delete_slide"}])
    pending = read.attempt("exclua este slide", actor_user_id="u1")
    assert pending.status is GovernedCapabilityStatus.CONFIRMATION_REQUIRED
    result = read.attempt(
        "",
        actor_user_id="u1",
        confirmation=_confirmation(pending),
        max_execution_stage="prepare",
    )
    assert "commit_proposal" not in [c[1] for c in port.calls]
    assert result.status is not GovernedCapabilityStatus.SUCCESS


# G. fast provider — stage max preserved, success unchanged
def test_r1_fast_provider_stage_max_and_success_unchanged():
    clock = [1000.0]
    port = _DeadlinePort(
        tools_by_specialist={"vista": VISTA_TOOLS}, clock=clock
    )
    read = _vista_listing(_interop(port))
    attempt = read.attempt(
        "liste", turn_deadline=_deadline(clock, 80.0)
    )
    assert attempt.status is GovernedCapabilityStatus.SUCCESS
    # With a large remaining budget the provider's configured stage
    # max applies unchanged — reduction-only, never widening.
    assert port.list_timeouts and all(
        t == DEFAULT_INVOCATION_TIMEOUT_SECONDS
        for t in port.list_timeouts
    )
    assert port.call_timeouts and all(
        0 < t <= DEFAULT_INVOCATION_TIMEOUT_SECONDS
        for t in port.call_timeouts
    )


# Interop seam: request timeout bounds list+call as ONE operation
def test_r1_interop_invoke_second_leg_budget_exhausted():
    """Inside SpecialistInterop.invoke the call leg receives only what
    the revalidation list left — an exhausted remainder fails with
    mcp_timeout instead of a fresh full timeout."""
    port = _DeadlinePort(
        tools_by_specialist={"vista": VISTA_TOOLS},
        real_list_sleep=0.05,
    )
    interop = _interop(port)
    with pytest.raises(SpecialistInteropError) as exc:
        interop.invoke(
            SpecialistInvocationRequest(
                specialist_id="vista",
                remote_capability="list_playlists",
                correlation_id="c1",
                arguments={},
                timeout_seconds=0.01,
            )
        )
    assert exc.value.code == MCP_TIMEOUT
    assert port.calls == []


# --- R1 live-equivalent: real wire timeout through real requests --------------
#
# Production-equivalent non-mutating evidence: a real DelpiMcpTransport
# issuing real requests.post calls against a real socket server that
# stalls — the bounded timeout must cut the wire operation at the
# granted budget, never the configured transport max.


def test_r1_mcp_wire_slow_server_bounded_by_call_timeout():
    """A stalled specialist cannot hold the turn: the per-call bound
    reaches requests.post and terminates near the granted budget."""
    from app.infrastructure.interoperability.mcp.transport import (
        DelpiMcpTransport,
    )

    serving = threading.Event()

    def stall(conn):
        try:
            conn.recv(65536)
            serving.set()
            # Never answer — a specialist wedged mid-turn.
            time.sleep(10)
        except OSError:
            pass
        finally:
            conn.close()

    port, done = _serve_forever(stall)
    transport = DelpiMcpTransport(
        f"http://127.0.0.1:{port}/mcp",
        timeout_seconds=30.0,
        bearer_token="t",
    )
    started = time.monotonic()
    with pytest.raises(SpecialistInteropError) as exc:
        transport.list_tools(timeout_seconds=0.5)
    elapsed = time.monotonic() - started
    assert exc.value.code == MCP_TIMEOUT
    # Near the granted 0.5s — nowhere near the configured 30s or the
    # server's 10s stall.
    assert elapsed < 3.0
    assert serving.is_set()
    done.wait(timeout=15.0)


def test_r1_mcp_wire_normal_path_unchanged():
    """Non-mutating normal path: a fast specialist still answers
    through the same bounded seam — contract unchanged."""
    from app.infrastructure.interoperability.mcp.transport import (
        DelpiMcpTransport,
    )

    def fast(conn):
        try:
            conn.recv(65536)
            body = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {"tools": []},
                }
            ).encode()
            conn.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/json\r\n"
                b"Content-Length: "
                + str(len(body)).encode()
                + b"\r\n\r\n"
                + body
            )
        except OSError:
            pass
        finally:
            conn.close()

    port, done = _serve_forever(fast)
    transport = DelpiMcpTransport(
        f"http://127.0.0.1:{port}/mcp",
        timeout_seconds=30.0,
        bearer_token="t",
    )
    started = time.monotonic()
    tools = transport.list_tools(timeout_seconds=5.0)
    elapsed = time.monotonic() - started
    assert tools == ()
    assert elapsed < 5.0
    done.wait(timeout=5.0)
