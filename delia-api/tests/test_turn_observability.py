"""DELIA-UX-CONTEXT-PANEL-...-01 (Prompt 5) — turn observability.

Covers the bounded request-scoped model-call ledger, the additive
``observability`` projection on ``InteractiveTurnResult``, honest
usage aggregation (reported/partial/unavailable — never fabricated),
governed-attempt accounting without double-counting, effective
composition mode (cri/deterministic/model vs. the configured flag),
and privacy bounds.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    InteractiveTurnRequest,
    InteractiveTurnResult,
)
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn,
    serialize_result,
)
from app.application.interaction.turn_observability import (
    COMPOSITION_CRI,
    COMPOSITION_DETERMINISTIC,
    COMPOSITION_MODEL,
    MAX_LEDGER_CALLS,
    MAX_STAGE_CHARS,
    USAGE_STATUS_PARTIAL,
    USAGE_STATUS_REPORTED,
    USAGE_STATUS_UNAVAILABLE,
    ModelCallLedger,
    ModelCallObservation,
    aggregate_usage,
    bind_turn_call_ledger,
    build_turn_observability,
    current_call_ledger,
    reset_turn_call_ledger,
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
from app.domain.evidence.model import ModelRef
from app.domain.interaction.model import GroundingStatus
from app.domain.model_invocation.model import (
    InvocationFinishStatus,
    ProviderExposureClass,
    UsageMetadata,
)
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="u1",
        name="User",
        email="u@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _request() -> InteractiveTurnRequest:
    return InteractiveTurnRequest(
        access_context=_context(), input_text="olá"
    )


def _result(*, usage=True, duration_ms=12):
    """A ModelInvocationResult-shaped stub the ledger consumes."""
    payload = ProviderInvocationPayload(
        structured_output={"answer": "ok", "limitations": []},
        generated_at=datetime.now(timezone.utc).isoformat(),
        usage=(
            UsageMetadata(
                input_units=100, output_units=20, unit_kind="tokens"
            )
            if usage
            else None
        ),
        duration_ms=duration_ms,
    )
    return payload


class _ResultStub:
    """Minimal ModelInvocationResult surface the ledger needs."""

    def __init__(self, *, usage, duration_ms):
        self.usage = usage
        self.duration_ms = duration_ms
        self.finish_status = InvocationFinishStatus.COMPLETED


# --- ledger unit tests -----------------------------------------------------


def test_ledger_records_usage_and_duration_verbatim():
    ledger = ModelCallLedger()
    ledger.record_result(
        stage="delia.stage.a",
        result=_ResultStub(
            usage=UsageMetadata(
                input_units=321, output_units=17, unit_kind="tokens"
            ),
            duration_ms=42,
        ),
        attempt=1,
    )
    (call,) = ledger.calls
    assert call.stage == "delia.stage.a"
    assert call.input_tokens == 321
    assert call.output_tokens == 17
    assert call.duration_ms == 42
    assert call.attempt == 1


def test_ledger_records_failed_call_without_fabricating_usage():
    ledger = ModelCallLedger()
    ledger.record_error(
        stage="delia.stage.b", finish_status="timeout", attempt=2
    )
    (call,) = ledger.calls
    assert call.finish_status == "timeout"
    assert call.input_tokens is None
    assert call.output_tokens is None


def test_ledger_is_bounded():
    ledger = ModelCallLedger()
    stub = _ResultStub(usage=None, duration_ms=None)
    for _ in range(MAX_LEDGER_CALLS + 5):
        ledger.record_result(stage="s", result=stub)
    assert len(ledger.calls) == MAX_LEDGER_CALLS


def test_ledger_unbound_returns_none():
    assert current_call_ledger() is None


def test_ledger_bind_and_reset_is_request_scoped():
    ledger = ModelCallLedger()
    token = bind_turn_call_ledger(ledger)
    try:
        assert current_call_ledger() is ledger
    finally:
        reset_turn_call_ledger(token)
    assert current_call_ledger() is None


# --- aggregation statuses ---------------------------------------------------


def _obs(**kwargs) -> ModelCallObservation:
    return ModelCallObservation(
        stage=kwargs.get("stage", "s"),
        attempt=kwargs.get("attempt", 1),
        finish_status=kwargs.get("finish_status", "completed"),
        duration_ms=kwargs.get("duration_ms"),
        input_tokens=kwargs.get("input_tokens"),
        output_tokens=kwargs.get("output_tokens"),
    )


def test_usage_provider_reported_when_all_calls_carry_usage():
    agg = aggregate_usage(
        (
            _obs(input_tokens=100, output_tokens=20),
            _obs(input_tokens=50, output_tokens=10),
        )
    )
    assert agg["status"] == USAGE_STATUS_REPORTED
    assert agg["input"] == 150
    assert agg["output"] == 30
    assert agg["total"] == 180


def test_usage_partial_when_any_call_lacks_usage():
    agg = aggregate_usage(
        (
            _obs(input_tokens=100, output_tokens=20),
            _obs(finish_status="timeout"),
        )
    )
    assert agg["status"] == USAGE_STATUS_PARTIAL
    # Known directions are still shown — the total is not invented.
    assert agg["input"] == 100
    assert agg["output"] == 20
    assert agg["total"] is None


def test_usage_unavailable_when_no_call_reports():
    agg = aggregate_usage((_obs(), _obs(finish_status="error")))
    assert agg["status"] == USAGE_STATUS_UNAVAILABLE
    assert agg["input"] is None
    assert agg["output"] is None
    assert agg["total"] is None


def test_usage_unavailable_for_zero_calls():
    agg = aggregate_usage(())
    assert agg["status"] == USAGE_STATUS_UNAVAILABLE


def test_partial_when_only_one_direction_reported():
    agg = aggregate_usage((_obs(input_tokens=80),))
    assert agg["status"] == USAGE_STATUS_PARTIAL
    assert agg["input"] == 80
    assert agg["output"] is None
    assert agg["total"] is None


# --- projection shape / privacy --------------------------------------------


def test_projection_is_bounded_and_never_carries_payload():
    obs = build_turn_observability(
        model_ref=ModelRef(
            model_id="qwen2.5:3b" + "x" * MAX_STAGE_CHARS,
            version="v1",
            owner_ref="owner",
            provider_ref="ollama",
        ),
        response_mode="cri",
        composition_mode=COMPOSITION_CRI,
        calls=(_obs(input_tokens=10, output_tokens=5),),
        duration_ms=250,
        governed_attempts=2,
    )
    assert obs["model"]["id"].endswith("x" * 40)
    assert len(obs["model"]["id"]) <= MAX_STAGE_CHARS
    # Provider identity never crosses the wire (canonical leak gate);
    # owner attribution is the safe surface.
    assert "provider" not in obs["model"]
    assert obs["model"]["owner"] == "owner"
    assert obs["composition_mode"] == COMPOSITION_CRI
    assert obs["response_mode"] == "cri"
    assert obs["duration_ms"] == 250
    assert obs["governed_attempts"] == 2
    assert obs["model_calls"] == 1
    assert obs["cost"] == {"status": "unavailable"}
    # No authority, credential, prompt, or raw payload surface.
    forbidden = {
        "prompt",
        "instruction",
        "instruction_content",
        "input_text",
        "chain_of_thought",
        "api_key",
        "token",
        "secret",
        "raw_payload",
        "authorization",
    }
    assert forbidden.isdisjoint(obs.keys())
    (call,) = obs["calls"]
    assert forbidden.isdisjoint(call.keys())


def test_projection_handles_absent_model_ref_and_missing_fields():
    obs = build_turn_observability(
        model_ref=None,
        response_mode="baseline",
        composition_mode=COMPOSITION_DETERMINISTIC,
        calls=(),
        duration_ms=None,
        governed_attempts=1,
    )
    assert obs["model"] is None
    assert obs["duration_ms"] is None
    assert obs["model_calls"] == 0
    assert obs["tokens"]["status"] == USAGE_STATUS_UNAVAILABLE


def test_observation_projection_bounds_negative_and_nonints():
    call = ModelCallObservation(
        stage="x" * (MAX_STAGE_CHARS + 50),
        attempt=-3,
        finish_status="completed",
        duration_ms=-1,
        input_tokens=None,
        output_tokens=None,
    )
    proj = call.to_projection()
    assert len(proj["stage"]) == MAX_STAGE_CHARS
    assert proj["attempt"] is None
    assert proj["duration_ms"] is None


# --- handler-level integration ---------------------------------------------


class _UsageAdapter:
    """Provider adapter double that reports typed usage."""

    ADAPTER_KIND = "TEST_ONLY"
    EXPOSURE_CLASS = ProviderExposureClass.TEST_ONLY

    def __init__(self, *, usage: UsageMetadata | None):
        self._usage = usage
        self.calls = 0

    @property
    def adapter_kind(self):
        return self.ADAPTER_KIND

    @property
    def exposure_class(self):
        return self.EXPOSURE_CLASS

    def invoke(self, request: ModelInvocationRequest):
        self.calls += 1
        return _result(usage=self._usage is not None)


class _FailingAdapter:
    ADAPTER_KIND = "TEST_ONLY"
    EXPOSURE_CLASS = ProviderExposureClass.TEST_ONLY

    def __init__(self):
        self.calls = 0

    @property
    def adapter_kind(self):
        return self.ADAPTER_KIND

    @property
    def exposure_class(self):
        return self.EXPOSURE_CLASS

    def invoke(self, request: ModelInvocationRequest):
        self.calls += 1
        raise ModelInvocationError(TIMEOUT, "boom")


def _usage_adapter(with_usage=True):
    class _A(_UsageAdapter):
        def __init__(self):
            super().__init__(
                usage=(
                    UsageMetadata(
                        input_units=111,
                        output_units=22,
                        unit_kind="tokens",
                    )
                    if with_usage
                    else None
                )
            )

        def invoke(self, request: ModelInvocationRequest):
            self.calls += 1
            return ProviderInvocationPayload(
                structured_output={"answer": "ok", "limitations": []},
                generated_at=datetime.now(timezone.utc).isoformat(),
                usage=self._usage,
                duration_ms=15,
            )

    return _A()


def test_conversational_result_exposes_observability():
    adapter = _usage_adapter()
    handler = HandleInteractiveConversationTurn(InvokeModel(adapter))
    result = handler.execute(_request())
    assert result.observability is not None
    obs = result.observability
    assert obs["composition_mode"] == COMPOSITION_MODEL
    assert obs["model_calls"] == 1
    assert adapter.calls == 1
    assert obs["tokens"]["status"] == USAGE_STATUS_REPORTED
    assert obs["tokens"]["input"] == 111
    assert obs["tokens"]["output"] == 22
    assert obs["tokens"]["total"] == 133
    (call,) = obs["calls"]
    assert call["stage"] == "delia.interaction.turn"
    assert call["duration_ms"] == 15
    assert obs["cost"]["status"] == "unavailable"
    # Model identity is safely exposable metadata only.
    assert obs["model"]["id"]
    assert obs["model"]["owner"] == "DELPI"


def test_conversational_result_without_usage_marks_unavailable():
    adapter = _usage_adapter(with_usage=False)
    handler = HandleInteractiveConversationTurn(InvokeModel(adapter))
    result = handler.execute(_request())
    obs = result.observability
    # Call counted; tokens honest — never zeroed.
    assert obs["model_calls"] == 1
    assert obs["tokens"]["status"] == USAGE_STATUS_UNAVAILABLE
    assert obs["tokens"]["input"] is None
    assert obs["tokens"]["total"] is None


def test_serialize_result_carries_observability():
    handler = HandleInteractiveConversationTurn(
        InvokeModel(_usage_adapter())
    )
    result = handler.execute(_request())
    wire = serialize_result(result)
    assert wire["observability"] is not None
    assert wire["observability"]["tokens"]["input"] == 111
    assert wire["observability"]["composition_mode"] == "model"
    # Legacy keys untouched (additive contract).
    assert "content" in wire
    assert "presentation" in wire


def test_serialize_result_keeps_absent_observability_none():
    result = InteractiveTurnResult(
        session_id="s",
        user_turn_id="u",
        result_turn_id="r",
        content="c",
        epistemic_class=None,
        limitations=(),
        generated_at="t",
        model_invocation_id=None,
        grounding_status=GroundingStatus.NON_GROUNDED,
    )
    wire = serialize_result(result)
    assert wire["observability"] is None


def test_orchestrated_attempt_carries_composition_and_attempts():
    """A governed attempt marked cri + multi-attempt projects
    effective composition and honest attempt accounting."""

    class _Orchestration:
        def attempt(self, *_args, **_kwargs):
            from app.domain.interaction.model import (
                TurnKind as _TK,
            )  # noqa: F401

            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.AUTHZ_DENIED,
                correlation_id="c1",
                content="negado",
                composition_mode="deterministic",
                governed_attempts=2,
            )

    handler = HandleInteractiveConversationTurn(
        InvokeModel(DeterministicTestAdapter()),
        capability_orchestration=_Orchestration(),
    )
    result = handler.execute(_request())
    obs = result.observability
    assert obs["composition_mode"] == "deterministic"
    assert obs["governed_attempts"] == 2


def test_cri_composition_mode_surfaces_when_marked():
    from app.domain.specialist_interop.model import (
        InteropProtocol,
        SpecialistOutcome,
        SpecialistResultProvenance,
        SpecialistResultStatus,
    )

    class _Orchestration:
        def attempt(self, *_args, **_kwargs):
            outcome = SpecialistOutcome(
                status=SpecialistResultStatus.COMPLETED,
                provenance=SpecialistResultProvenance(
                    specialist_id="sp",
                    remote_name="cap",
                    protocol=InteropProtocol.MCP,
                    correlation_id="c1",
                    observed_at="2026-01-01T00:00:00Z",
                ),
                content_text="resposta",
            )
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.SUCCESS,
                correlation_id="c1",
                outcome=outcome,
                content="resposta",
                composition_mode="cri",
                governed_attempts=1,
            )

    handler = HandleInteractiveConversationTurn(
        InvokeModel(DeterministicTestAdapter()),
        capability_orchestration=_Orchestration(),
    )
    result = handler.execute(_request())
    assert result.observability["composition_mode"] == "cri"


def test_no_orchestration_conversational_model_mode():
    handler = HandleInteractiveConversationTurn(
        InvokeModel(DeterministicTestAdapter())
    )
    result = handler.execute(_request())
    assert result.observability["composition_mode"] == "model"


def test_timeout_call_counted_without_fabricated_usage():
    """A model call that timed out is counted as a call — usage stays
    unavailable, never zeroed (RQ-P5-06/07 honest absence)."""

    class _NotApplicable:
        def attempt(self, *_args, **_kwargs):
            return GovernedCapabilityAttempt(
                status=GovernedCapabilityStatus.NOT_APPLICABLE,
                correlation_id="c1",
                governed_attempts=1,
            )

    adapter = _FailingAdapter()
    handler = HandleInteractiveConversationTurn(
        InvokeModel(adapter),
        capability_orchestration=_NotApplicable(),
    )
    result = handler.execute(_request())
    obs = result.observability
    assert adapter.calls == 1
    assert obs["model_calls"] == 1
    (call,) = obs["calls"]
    assert call["finish_status"] == "timeout"
    assert call["input_tokens"] is None
    assert obs["tokens"]["status"] == USAGE_STATUS_UNAVAILABLE
    assert obs["composition_mode"] == "deterministic"


# --- stage-6 budget attribution ---------------------------------------------


def test_budget_remaining_recorded_and_projected():
    ledger = ModelCallLedger()
    result = _result()
    ledger.record_result(
        stage="s", result=result, attempt=1, budget_remaining_ms=17200
    )
    (call,) = ledger.calls
    assert call.budget_remaining_ms == 17200
    obs = build_turn_observability(
        model_ref=None,
        response_mode="baseline",
        composition_mode=COMPOSITION_DETERMINISTIC,
        calls=ledger.calls,
        duration_ms=None,
        governed_attempts=1,
    )
    assert obs["calls"][0]["budget_remaining_ms"] == 17200


def test_operational_calls_separated_from_model_elapsed():
    ledger = ModelCallLedger()
    ledger.record_operational(
        capability="discover_delpi_information",
        duration_ms=412,
        finish_status="completed",
    )
    ledger.record_operational(
        capability="evidence_read",
        duration_ms=88,
        finish_status="error",
    )
    calls = (
        _obs(duration_ms=5000),
        _obs(duration_ms=3000),
    )
    obs = build_turn_observability(
        model_ref=None,
        response_mode="baseline",
        composition_mode=COMPOSITION_DETERMINISTIC,
        calls=calls,
        duration_ms=9500,
        governed_attempts=1,
        operational_calls=ledger.operational_calls,
    )
    assert obs["elapsed_ms"]["model"] == 8000
    assert obs["elapsed_ms"]["operational"] == 500
    assert obs["elapsed_ms"]["other"] == 1000
    assert len(obs["operational_calls"]) == 2
    assert obs["operational_calls"][1]["finish_status"] == "error"


def test_timeout_source_coarse_and_once():
    ledger = ModelCallLedger()
    ledger.record_terminal_timeout("budget")
    ledger.record_terminal_timeout("model")  # first wins
    ledger.record_terminal_timeout("not-a-source")  # rejected
    obs = build_turn_observability(
        model_ref=None,
        response_mode="baseline",
        composition_mode=COMPOSITION_DETERMINISTIC,
        calls=(),
        duration_ms=30000,
        governed_attempts=1,
        timeout_source=ledger.timeout_source,
    )
    assert obs["timeout_source"] == "budget"


def test_composition_elapsed_accumulates():
    ledger = ModelCallLedger()
    ledger.record_composition(4)
    ledger.record_composition(2)
    obs = build_turn_observability(
        model_ref=None,
        response_mode="cri",
        composition_mode=COMPOSITION_CRI,
        calls=(),
        duration_ms=100,
        governed_attempts=1,
        composition_ms=ledger.composition_ms,
    )
    assert obs["elapsed_ms"]["composition"] == 6
    assert obs["elapsed_ms"]["other"] == 94


def test_elapsed_other_none_without_total():
    obs = build_turn_observability(
        model_ref=None,
        response_mode="baseline",
        composition_mode=COMPOSITION_DETERMINISTIC,
        calls=(_obs(duration_ms=100),),
        duration_ms=None,
        governed_attempts=1,
    )
    assert obs["elapsed_ms"]["model"] == 100
    assert obs["elapsed_ms"]["other"] is None
    assert obs["timeout_source"] is None
    assert obs["operational_calls"] == []
