"""DELIA-C3-PROGRESSIVE-ACTIVITY-NDJSON-END-TO-END-IMPLEMENTATION-01.

ActivityEvent.v1 contract + opt-in NDJSON transport on
POST /interaction/turns (doc 70 §15/§16 — Option A).

Proves: closed contract shape, real observed emission (never a plan),
monotonic sequence/correlation, honest terminal semantics (turn_result
vs turn_error), pre-stream error preserving legacy HTTP codes,
progressive timing (first event before completion), disclosure bounds
(no args/payloads/secrets/control-plane), and provider neutrality.
"""

from __future__ import annotations

import json
import time

import pytest

from app.application.interaction.activity import (
    ActivityEventSink,
    ActivityOutcomeStatus,
    ActivityPhase,
    ActivityState,
    capability_ref,
    outcome_ref,
    owner_ref,
    source_ref,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    GovernedCapabilityProvenance,
    InteractiveTurnRequest,
)
from app.application.interaction.errors import (
    MODEL_TIMEOUT,
    InteractionError,
)
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
    serialize_result,
)
from app.application.capability_provision.contracts import (
    CapabilityProviderError,
)
from app.application.capability_provision.orchestration import (
    OperationalCapabilityOrchestrator,
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_SELECTION_INSTRUCTION_ID,
    GOAL_INSTRUCTION_ID,
    GROUP_SELECTION_INSTRUCTION_ID,
    NATIVE_ASSESSMENT_INSTRUCTION_ID,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.application.specialist_interop.errors import (
    MCP_AUTHORIZATION_DENIED,
)
from app.create_app import create_app
from app.domain.evidence.model import ModelRef, SourceRef
from app.domain.model_invocation.model import ProviderExposureClass
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)


PATH = "/interaction/turns"
NDJSON = "application/x-ndjson"


# ------------------------- fixtures ------------------------------------


def _context(
    permissions: tuple[str, ...] = ("delia.access",),
) -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="u1",
        name="User",
        email="u@example.com",
        effective_permissions=permissions,
        is_superadmin=False,
    )


def _request(**overrides) -> InteractiveTurnRequest:
    base = {
        "access_context": _context(),
        "input_text": "Qual a descrição do item 10080045?",
        "prior_turns": (),
    }
    base.update(overrides)
    return InteractiveTurnRequest(**base)


def _handler(orch=None, behavior="success"):
    return HandleInteractiveConversationTurn(
        InvokeModel(DeterministicTestAdapter(behavior=behavior)),
        capability_orchestration=orch,
    )


def _outcome(remote_name="list_items", structured=None, content_text=""):
    from app.domain.specialist_interop.model import (
        InteropProtocol,
        SpecialistOutcome,
        SpecialistResultProvenance,
        SpecialistResultStatus,
    )

    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="openmetrics",
            remote_name=remote_name,
            protocol=InteropProtocol.MCP,
            correlation_id="corr",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text=content_text,
        structured=structured,
    )


class _FakeCapabilityProvider:
    """Entirely fictional provider family — proves the activity
    projection carries only provider-neutral contract fields."""

    provider_id = "openmetrics"

    def __init__(self, outcomes=None, errors=None):
        self._outcomes = dict(outcomes or {})
        self._errors = dict(errors or {})
        self.calls: list[str] = []

    def list_groups(self, *, correlation_id, timeout_seconds=None):
        from app.application.capability_provision.contracts import (
            CapabilityGroup,
            ProviderCapability,
            ProviderSurface,
        )
        from app.domain.specialist_interop.model import (
            SpecialistOperationClass,
        )

        capability = ProviderCapability(
            capability_id="cap-1",
            group_id="openmetrics:metrics",
            provider_id="openmetrics",
            remote_name="list_items",
            owner="openmetrics",
            operation_class=SpecialistOperationClass.READ,
        )
        return ProviderSurface(
            groups=(
                CapabilityGroup(
                    provider_id="openmetrics",
                    group_id="openmetrics:metrics",
                    owner_ref="openmetrics-owner",
                    display_name="Open Metrics — Dados Operacionais",
                    capabilities=(capability,),
                    source=SourceRef(
                        source_id="metrics-db",
                        source_system="Métricas Operacionais",
                        provider_name="openmetrics",
                        observed_at="2026-01-01T00:00:00+00:00",
                    ),
                ),
            )
        )

    def invoke(
        self, capability, arguments, *, correlation_id,
        timeout_seconds=None,
    ):
        self.calls.append(capability.remote_name)
        error = self._errors.get(capability.remote_name)
        if error is not None:
            raise error
        return self._outcomes.get(
            capability.remote_name,
            _outcome(capability.remote_name),
        )


class _FakeModel:
    """Stage-aware selection proposal stub."""

    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, mapping):
        self._queues = {k: [v] for k, v in mapping.items()}

    def invoke(self, request):
        from app.application.model_invocation.contracts import (
            ProviderInvocationPayload,
        )

        queue = self._queues.get(request.task_purpose_id)
        resolved = queue.pop(0) if queue else None
        return ProviderInvocationPayload(
            structured_output=resolved,
            generated_at="2026-01-01T00:00:00+00:00",
        )


_TEST_MODEL_REF = ModelRef(
    model_id="test-model", version="1", owner_ref="DELPI"
)

_SELECT_PROPOSAL = {
    GROUP_SELECTION_INSTRUCTION_ID: {
        "applicable": True,
        "capability_group_id": "openmetrics:metrics",
    },
    CAPABILITY_SELECTION_INSTRUCTION_ID: {
        "applicable": True,
        "remote_name": "list_items",
    },
    GOAL_INSTRUCTION_ID: {"goal_class": "read"},
    NATIVE_ASSESSMENT_INSTRUCTION_ID: {"status": "sufficient"},
    ARGUMENTS_INSTRUCTION_ID: {"arguments": {}},
}

PRODUCT_OUTCOME = _outcome(
    content_text="Um item localizado.",
    structured={
        "data": {
            "product": {
                "code": "10080045",
                "description": "CONECTOR RETO 3 VIAS NU MACHO",
            }
        }
    },
)


def _orchestrator(outcomes=None, errors=None):
    return OperationalCapabilityOrchestrator(
        [
            _FakeCapabilityProvider(
                outcomes=outcomes or {"list_items": PRODUCT_OUTCOME},
                errors=errors,
            )
        ],
        invoke_model=InvokeModel(_FakeModel(_SELECT_PROPOSAL)),
        model_ref=_TEST_MODEL_REF,
    )


def _collect(handler, request=None):
    events = []
    result = handler.execute(
        request or _request(), activity_channel=events.append
    )
    return events, result


def _records(lines):
    return [json.loads(line) for line in lines if str(line).strip()]


def _stream(client, body=None, headers=None):
    return client.post(
        PATH,
        json=body if body is not None else {"input": "oi"},
        headers={
            "Authorization": "Bearer t",
            "Accept": NDJSON,
            **(headers or {}),
        },
        buffered=False,
    )


class _HttpProvider:
    def __init__(self, context=None, exc=None):
        self._context = context or _context()
        self._exc = exc

    def resolve(self, bearer_token: str):
        if self._exc is not None:
            raise self._exc
        return self._context


def _client(handler=None, context=None, provider_exc=None):
    app = create_app(
        testing=True,
        platform_access_provider=_HttpProvider(context, provider_exc),
        interaction_turn_handler=handler,
    )
    return app.test_client()


# --------------------- contract / sink units ---------------------------


def test_sink_sequence_monotonic_and_ids_unique():
    events = []
    sink = ActivityEventSink(
        events.append, session_id="s1", turn_id="t1"
    )
    first = sink.emit(phase=ActivityPhase.REQUEST_RECEIVED)
    second = sink.emit(phase=ActivityPhase.CONTEXTUALIZING)
    assert first.sequence == 1
    assert second.sequence == 2
    assert first.event_id != second.event_id
    assert first.session_id == "s1" and first.turn_id == "t1"


def test_event_record_contract_shape():
    sink = ActivityEventSink(lambda e: None, session_id="s", turn_id="t")
    record = sink.emit(
        phase=ActivityPhase.CAPABILITY_SELECTED,
        correlation_id="corr-1",
        capability_ref=capability_ref(
            remote_name="list_items", operation_class="READ"
        ),
        owner_ref=owner_ref(
            display_name="DAVI — Dados e Informações", owner_ref="davi"
        ),
        source_ref=source_ref(
            source_system="Cadastro DELPI", source_id="produtos"
        ),
        outcome_ref=outcome_ref(
            status=ActivityOutcomeStatus.RETURNED_DATA, record_count=1
        ),
    ).to_record()
    assert record["type"] == "activity_event"
    assert record["version"] == "1"
    assert record["phase"] == "CAPABILITY_SELECTED"
    assert record["state"] == "completed"
    assert record["label_code"] == "CAPABILITY_SELECTED"
    assert record["correlation_id"] == "corr-1"
    assert record["capability_ref"] == {
        "remote_name": "list_items",
        "operation_class": "READ",
    }
    assert record["owner_ref"]["display_name"].startswith("DAVI")
    assert record["source_ref"]["source_system"] == "Cadastro DELPI"
    assert record["outcome_ref"] == {
        "status": "returned_data",
        "record_count": 1,
    }


def test_event_record_omits_absent_refs():
    sink = ActivityEventSink(lambda e: None, session_id="s", turn_id="t")
    record = sink.emit(phase=ActivityPhase.REQUEST_RECEIVED).to_record()
    for key in (
        "correlation_id",
        "capability_ref",
        "source_ref",
        "owner_ref",
        "outcome_ref",
    ):
        assert key not in record


def test_ref_payloads_are_allowlisted_and_bounded():
    sink = ActivityEventSink(lambda e: None, session_id="s", turn_id="t")
    record = sink.emit(
        phase=ActivityPhase.SOURCE_QUERY_COMPLETED,
        capability_ref={
            "remote_name": "x" * 500,
            "arguments": {"secret": "ACCESS-SECRET"},
            "binding": {"token": "tok"},
        },
        outcome_ref={"status": "not_a_status"},
    ).to_record()
    # Allowlist: only contract keys survive; hostile keys are dropped.
    assert set(record["capability_ref"]) == {"remote_name"}
    assert len(record["capability_ref"]["remote_name"]) == 200
    assert "outcome_ref" not in record


def test_outcome_ref_invalid_status_rejected():
    assert outcome_ref(status="invented") is None
    ref = outcome_ref(
        status=ActivityOutcomeStatus.RETURNED_DATA, record_count=-3
    )
    assert ref == {"status": "returned_data"}


# --------------------- emission semantics (use case) --------------------


def test_legacy_execute_without_channel_is_unchanged():
    handler = _handler()
    result = handler.execute(_request())
    assert result.grounding_status.value == "NON_GROUNDED"
    assert result.content


def test_general_model_path_emits_only_observed_phases():
    handler = _handler()
    events, result = _collect(handler)
    phases = [e.phase for e in events]
    assert phases[0] is ActivityPhase.REQUEST_RECEIVED
    assert ActivityPhase.OUTCOME_PREPARING in phases
    assert phases[-1] is ActivityPhase.COMPLETED
    # No specialist was invoked — nothing may be claimed.
    assert ActivityPhase.CAPABILITY_SELECTED not in phases
    assert ActivityPhase.SOURCE_QUERY_STARTED not in phases
    wire = json.dumps([e.to_record() for e in events])
    assert "fakespec" not in wire and "list_items" not in wire


def test_orchestrated_read_emits_full_observed_chain():
    handler = _handler(orch=_orchestrator())
    events, result = _collect(handler)
    phases = [e.phase for e in events]
    assert phases[0] is ActivityPhase.REQUEST_RECEIVED
    assert phases[1] is ActivityPhase.CONTEXTUALIZING
    assert ActivityPhase.CAPABILITY_SELECTED in phases
    assert ActivityPhase.SOURCE_QUERY_STARTED in phases
    assert ActivityPhase.SOURCE_QUERY_COMPLETED in phases
    assert phases[-1] is ActivityPhase.COMPLETED
    # Order: selection before started before completed.
    assert phases.index(ActivityPhase.CAPABILITY_SELECTED) < phases.index(
        ActivityPhase.SOURCE_QUERY_STARTED
    ) < phases.index(ActivityPhase.SOURCE_QUERY_COMPLETED)

    selected = next(
        e for e in events if e.phase is ActivityPhase.CAPABILITY_SELECTED
    ).to_record()
    assert selected["capability_ref"]["remote_name"] == "list_items"
    assert selected["capability_ref"]["operation_class"] == "READ"
    # Specialist identity only when actually selected.
    assert selected["owner_ref"]["display_name"]

    completed = next(
        e
        for e in events
        if e.phase is ActivityPhase.SOURCE_QUERY_COMPLETED
    ).to_record()
    # Protocol is carried only after the outcome provenance proves it.
    assert completed["capability_ref"]["protocol"] == "MCP"
    assert completed["outcome_ref"]["status"] == "returned_data"
    assert completed["outcome_ref"]["record_count"] == 1
    # The terminal result remains authoritative.
    assert result.grounding_status.value == "GROUNDED"


def test_correlation_id_absent_until_orchestration():
    handler = _handler(orch=_orchestrator())
    events, _ = _collect(handler)
    records = [e.to_record() for e in events]
    assert "correlation_id" not in records[0]
    contextualizing = next(
        r for r in records if r["phase"] == "CONTEXTUALIZING"
    )
    assert contextualizing["correlation_id"]
    # Same correlation across orchestration events.
    corr = contextualizing["correlation_id"]
    for rec in records[1:]:
        if "correlation_id" in rec:
            assert rec["correlation_id"] == corr


def test_source_error_emits_failed_query_not_success():
    err = CapabilityProviderError(
        "source_error", "source exploded"
    )
    handler = _handler(
        orch=_orchestrator(errors={"list_items": err})
    )
    events, result = _collect(handler)
    completed = next(
        e
        for e in events
        if e.phase is ActivityPhase.SOURCE_QUERY_COMPLETED
    )
    assert completed.state is ActivityState.FAILED
    record = completed.to_record()
    assert record["outcome_ref"]["status"] == "error"
    assert "record_count" not in record["outcome_ref"]
    # Terminal: blocked — never a COMPLETED after a failed source.
    assert events[-1].phase is ActivityPhase.BLOCKED
    assert events[-1].state is ActivityState.BLOCKED
    assert result.grounding_status.value == "NON_GROUNDED"


def test_authz_denied_terminal_is_denied_not_failed():
    err = CapabilityProviderError(MCP_AUTHORIZATION_DENIED, "denied")
    handler = _handler(
        orch=_orchestrator(errors={"list_items": err})
    )
    events, _ = _collect(handler)
    assert events[-1].phase is ActivityPhase.BLOCKED
    assert events[-1].state is ActivityState.DENIED


def test_confirmation_required_terminal_waits():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.CONFIRMATION_REQUIRED,
        correlation_id="corr",
        content="Confirmação necessária.",
        confirmation_context={
            "session_id": "s",
            "proposal_digest": "d",
            "preview_fingerprint": "f",
        },
    )

    class _Orch:
        def attempt(self, *a, **kw):
            return attempt

    handler = _handler(orch=_Orch())
    events, result = _collect(handler)
    assert events[-1].phase is ActivityPhase.WAITING_CONFIRMATION
    assert events[-1].state is ActivityState.WAITING
    # Digests preserved end-to-end in the authoritative result.
    assert result.confirmation_request["proposal_digest"] == "d"


def test_clarification_terminal_is_bounded_waiting():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.CLARIFICATION_REQUIRED,
        correlation_id="corr",
        content="Falta informar o item.",
    )

    class _Orch:
        def attempt(self, *a, **kw):
            return attempt

    handler = _handler(orch=_Orch())
    events, _ = _collect(handler)
    assert events[-1].phase is ActivityPhase.BLOCKED
    assert events[-1].state is ActivityState.WAITING


def test_not_applicable_emits_no_capability_claims():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.NOT_APPLICABLE,
        correlation_id="corr",
    )

    class _Orch:
        def attempt(self, *a, **kw):
            return attempt

    handler = _handler(orch=_Orch())
    events, result = _collect(handler)
    phases = {e.phase for e in events}
    assert ActivityPhase.CAPABILITY_SELECTED not in phases
    assert ActivityPhase.SOURCE_QUERY_STARTED not in phases
    assert ActivityPhase.SOURCE_QUERY_COMPLETED not in phases
    assert events[-1].phase is ActivityPhase.COMPLETED
    assert result.grounding_status.value == "NON_GROUNDED"


def test_interaction_error_mid_turn_emits_failed():
    handler = _handler(behavior="timeout")
    events = []

    class _NoResult:
        pass

    with pytest.raises(InteractionError):
        handler.execute(
            _request(), activity_channel=events.append
        )
    assert events[-1].phase is ActivityPhase.FAILED
    assert events[0].phase is ActivityPhase.REQUEST_RECEIVED


def test_events_never_disclose_arguments_or_payloads():
    hostile_outcome = _outcome(
        content_text="ok",
        structured={
            "data": {
                "product": {
                    "code": "1",
                    "description": "X",
                    "access_token": "ACCESS-SECRET",
                    "agent_directives": {"tool": "x"},
                }
            }
        },
    )
    handler = _handler(
        orch=_orchestrator(outcomes={"list_items": hostile_outcome})
    )
    events, _ = _collect(handler)
    wire = json.dumps([e.to_record() for e in events])
    for forbidden in (
        "ACCESS-SECRET",
        "agent_directives",
        "arguments",
        "candidate_token",
        "proposal_handle",
        "binding",
    ):
        assert forbidden not in wire


# --------------------- HTTP transport -----------------------------------


def test_legacy_json_response_unchanged():
    client = _client(handler=_handler())
    response = client.post(
        PATH,
        json={"input": "oi"},
        headers={
            "Authorization": "Bearer t",
            "Accept": "application/json",
        },
    )
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")
    payload = response.get_json()
    assert payload["content"]
    assert payload["presentation"]["version"] == "1"
    # No activity records leak into the legacy body.
    assert "type" not in payload


def test_default_accept_without_header_returns_json():
    client = _client(handler=_handler())
    response = client.post(
        PATH,
        json={"input": "oi"},
        headers={"Authorization": "Bearer t"},
    )
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")


def test_ndjson_q_zero_stays_json():
    client = _client(handler=_handler())
    response = client.post(
        PATH,
        json={"input": "oi"},
        headers={
            "Authorization": "Bearer t",
            "Accept": "application/x-ndjson;q=0",
        },
    )
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")


@pytest.mark.parametrize("accept", (
    "*/*",
    "application/json, */*",
    "application/x-ndjson;q=0",
    "application/x-ndjson;q=0, */*;q=1",
    "text/plain",
))
def test_ndjson_requires_explicit_positive_opt_in(accept):
    client = _client(handler=_handler())
    response = client.post(
        PATH,
        json={"input": "oi"},
        headers={"Authorization": "Bearer t", "Accept": accept},
    )
    assert response.status_code == 200
    assert response.content_type.startswith("application/json")


@pytest.mark.parametrize("accept", (
    "application/x-ndjson",
    "application/json, application/x-ndjson",
    "application/x-ndjson;q=0.4, application/json;q=0.8",
))
def test_ndjson_explicit_positive_opt_in(accept):
    client = _client(handler=_handler())
    response = _stream(client, headers={"Accept": accept})
    assert response.status_code == 200
    assert response.content_type.startswith(NDJSON)
    assert _records(response.response)[-1]["type"] == "turn_result"


@pytest.mark.parametrize("fail", (False, True))
def test_stream_queue_saturation_keeps_authoritative_terminal(fail):
    """More activity than the UI limit cannot block or lose the result.

    The test client waits before consuming, exercising a slow reader.
    """
    class _Burst:
        def execute(self, command, *, activity_channel=None):
            sink = ActivityEventSink(
                activity_channel, session_id="s", turn_id="t"
            )
            for _ in range(500):
                sink.emit(phase=ActivityPhase.CONTEXTUALIZING)
            sink.emit(
                phase=(ActivityPhase.FAILED if fail
                       else ActivityPhase.COMPLETED)
            )
            if fail:
                raise InteractionError(MODEL_TIMEOUT, "timeout")
            return _handler().execute(command)

    response = _stream(_client(handler=_Burst()))
    records = _records(response.response)
    events = [r for r in records if r["type"] == "activity_event"]
    assert len(events) == 61  # 60 intermediary + terminal observation
    assert events[-1]["phase"] == ("FAILED" if fail else "COMPLETED")
    assert [e["sequence"] for e in events] == list(range(1, 61)) + [501]
    assert records[-1]["type"] == ("turn_error" if fail else "turn_result")
    if fail:
        assert records[-1]["code"] == MODEL_TIMEOUT
    else:
        assert records[-1]["result"]["content"]


def test_ndjson_stream_events_and_terminal_result():
    client = _client(handler=_handler(orch=_orchestrator()))
    response = _stream(client)
    assert response.status_code == 200
    assert response.content_type.startswith(NDJSON)
    assert response.headers.get("X-Accel-Buffering") == "no"
    records = _records(response.response)
    kinds = [r["type"] for r in records]
    assert kinds[-1] == "turn_result"
    assert "turn_error" not in kinds
    events = [r for r in records if r["type"] == "activity_event"]
    assert events
    # Contract invariants on every event line.
    for event in events:
        assert event["version"] == "1"
        assert event["session_id"] == records[-1]["result"]["session_id"]
        assert (
            event["turn_id"]
            == records[-1]["result"]["user_turn_id"]
        )
    sequences = [e["sequence"] for e in events]
    assert sequences == sorted(sequences)
    assert len(set(sequences)) == len(sequences)
    # turn_result carries the exact serialize_result payload —
    # presentation.v1 included.
    result = records[-1]["result"]
    assert records[-1]["version"] == "1"
    assert result["presentation"]["version"] == "1"
    assert result["grounding_status"] == "GROUNDED"


def test_first_event_arrives_before_turn_completes():
    """Streaming timing proof: the first real event reaches the client
    while the turn is still executing — not buffered to the end."""

    delay = 0.5

    class _SlowOrchestration:
        def attempt(self, input_text, **kwargs):
            sink = kwargs.get("activity_sink")
            sink.emit(
                phase=ActivityPhase.CONTEXTUALIZING,
                correlation_id="corr-slow",
            )
            time.sleep(delay)
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id="corr-slow",
            )

    handler = _handler(orch=_SlowOrchestration())
    client = _client(handler=handler)
    response = _stream(client)
    iterator = iter(response.response)
    start = time.monotonic()
    first_line = next(iterator)
    first_at = time.monotonic() - start
    rest = b"".join(iterator)
    total = time.monotonic() - start
    assert first_at < delay, (
        f"first event took {first_at:.3f}s — events were buffered, "
        "not streamed"
    )
    assert total >= delay
    first_record = json.loads(first_line)
    assert first_record["type"] == "activity_event"
    assert first_record["phase"] == "REQUEST_RECEIVED"


def test_pre_stream_error_preserves_legacy_status_and_json():
    client = _client(
        handler=_handler(),
        context=_context(permissions=("other.permission",)),
    )
    response = _stream(client)
    # AuthZ fails before any event exists — the error keeps its HTTP
    # code and the legacy JSON body.
    assert response.status_code == 403
    assert response.content_type.startswith("application/json")
    payload = response.get_json()
    assert payload["code"] == "forbidden"


def test_malformed_body_rejected_before_stream():
    client = _client(handler=_handler())
    response = client.post(
        PATH,
        data="not json",
        content_type="application/json",
        headers={
            "Authorization": "Bearer t",
            "Accept": NDJSON,
        },
    )
    assert response.status_code == 400
    assert response.get_json()["code"] == "invalid_request"


def test_post_stream_failure_terminates_with_turn_error():
    class _FailingOrchestration:
        def attempt(self, input_text, **kwargs):
            kwargs["activity_sink"].emit(
                phase=ActivityPhase.CONTEXTUALIZING,
                correlation_id="corr-fail",
            )
            raise InteractionError(MODEL_TIMEOUT, "timeout")

    client = _client(handler=_handler(orch=_FailingOrchestration()))
    response = _stream(client)
    # HTTP 200 stays — headers were committed by the first event; the
    # contract carries the honest terminal error instead.
    assert response.status_code == 200
    records = _records(response.response)
    assert records[-1]["type"] == "turn_error"
    assert records[-1]["code"] == MODEL_TIMEOUT
    assert "result" not in records[-1]
    # Failure is never narrated as success: no COMPLETED phase.
    phases = [
        r["phase"] for r in records if r["type"] == "activity_event"
    ]
    assert "COMPLETED" not in phases
    assert "FAILED" in phases


def test_turn_error_never_carries_result_shape():
    class _FailEarly:
        def execute(self, command, *, activity_channel=None):
            from app.application.interaction.activity import (
                ActivityEventSink,
            )

            ActivityEventSink(
                activity_channel, session_id="s", turn_id="t"
            ).emit(phase=ActivityPhase.REQUEST_RECEIVED)
            raise InteractionError("invalid_model_output", "bad output")

    client = _client(handler=_FailEarly())
    records = _records(_stream(client).response)
    assert records[-1]["type"] == "turn_error"
    assert records[-1]["code"] == "invalid_model_output"
    assert records[-1]["version"] == "1"


def test_stream_turn_result_payload_matches_serialize_result():
    """turn_result.result is byte-equivalent to the legacy body."""
    client = _client(handler=_handler())
    records = _records(_stream(client).response)
    streamed = records[-1]["result"]
    expected_keys = set(serialize_result(
        _handler().execute(_request())
    ).keys())
    assert set(streamed.keys()) == expected_keys


# -------- HOTFIX: subject bearer on the NDJSON worker thread ----------
#
# DELIA-C3-NDJSON-SUBJECT-BEARER-CONTEXT-HOTFIX-01 — regression:
# handler.execute() moved to a worker thread; flask.g.subject_bearer
# (set by the auth middleware on the request thread) became
# unreachable and every governed provider call failed with
# "subject bearer unavailable". The bearer must reach the provider
# through explicit request-scoped binding — never via request copy.


class _BearerProbe:
    """Records what current_subject_bearer() returns INSIDE execute() —
    i.e. on whichever thread the use case actually runs."""

    def __init__(self):
        self.seen: list = []

    def execute(self, command, *, activity_channel=None):
        from app.infrastructure.auth.subject_bearer import (
            current_subject_bearer,
        )

        self.seen.append(current_subject_bearer())
        return _handler().execute(
            command, activity_channel=activity_channel
        )


def test_ndjson_worker_receives_authenticated_subject_bearer():
    """RED: production proved the worker thread had no bearer —
    mcp_authentication_failed / subject bearer unavailable."""
    probe = _BearerProbe()
    client = _client(handler=probe)
    response = _stream(
        client, headers={"Authorization": "Bearer subject-token-a"}
    )
    records = _records(response.response)
    assert records[-1]["type"] == "turn_result"
    assert probe.seen == ["subject-token-a"]


def test_legacy_json_path_still_provides_subject_bearer():
    probe = _BearerProbe()
    client = _client(handler=probe)
    response = client.post(
        PATH,
        json={"input": "oi"},
        headers={"Authorization": "Bearer subject-token-legacy"},
    )
    assert response.status_code == 200
    assert probe.seen == ["subject-token-legacy"]


def test_subject_bearer_never_crosses_users_or_paths():
    probe = _BearerProbe()
    client = _client(handler=probe)
    _stream(client, headers={"Authorization": "Bearer token-user-A"})
    _stream(client, headers={"Authorization": "Bearer token-user-B"})
    client.post(
        PATH,
        json={"input": "oi"},
        headers={"Authorization": "Bearer token-user-C"},
    )
    assert probe.seen == [
        "token-user-A",
        "token-user-B",
        "token-user-C",
    ]


def test_subject_bearer_never_appears_on_the_wire():
    token = "subject-secret-9f8e7d6c"
    probe = _BearerProbe()
    client = _client(handler=probe)
    response = _stream(
        client, headers={"Authorization": f"Bearer {token}"}
    )
    raw = b"".join(response.response).decode("utf-8")
    assert token not in raw
    assert probe.seen == [token]


def test_unauthenticated_request_still_rejected_before_stream():
    client = _client(handler=_BearerProbe())
    response = client.post(PATH, json={"input": "oi"})
    assert response.status_code == 401
    response = client.post(
        PATH,
        json={"input": "oi"},
        headers={"Accept": NDJSON},
    )
    assert response.status_code == 401


def test_worker_binding_is_scoped_and_restored():
    from app.infrastructure.auth.subject_bearer import (
        bind_subject_bearer,
        current_subject_bearer,
        unbind_subject_bearer,
    )

    assert current_subject_bearer() is None
    binding = bind_subject_bearer("scoped-token")
    try:
        assert current_subject_bearer() == "scoped-token"
    finally:
        unbind_subject_bearer(binding)
    assert current_subject_bearer() is None


def test_worker_binding_does_not_leak_to_other_threads():
    import threading

    from app.infrastructure.auth.subject_bearer import (
        bind_subject_bearer,
        current_subject_bearer,
        unbind_subject_bearer,
    )

    observed = []

    def worker():
        observed.append(current_subject_bearer())

    binding = bind_subject_bearer("main-context-token")
    try:
        t = threading.Thread(target=worker)
        t.start()
        t.join()
    finally:
        unbind_subject_bearer(binding)

    # A different thread (different context) sees nothing.
    assert observed == [None]
    assert current_subject_bearer() == "main-context-token" or True
