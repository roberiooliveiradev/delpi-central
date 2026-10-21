"""CRI E1 — central response-intelligence ON/OFF (DELIA-CRI-E1-CENTRAL-ONOFF-01).

The switch is a single composition-resolved behavior decision (doc 73
§7, spec 75 §4.1): default OFF, fail-closed on absent/invalid config,
typed injection into the governed-outcome → response boundary. It
authorizes nothing and changes no output in this gate — OFF parity and
ON selection are both proven with the same governed fixture.
"""

from __future__ import annotations

import logging

import pytest

from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import (
    GovernedCapabilityProvenance,
    InteractiveTurnRequest,
)
from app.application.interaction.handle_interactive_turn import (
    DEFAULT_MODEL_REF,
    HandleInteractiveConversationTurn,
    serialize_result,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.application.platform_access import PlatformAccessContext
from app.composition.root_composer import _compose_turn_handler
from app.domain.evidence.model import SourceRef
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.model_invocation.deterministic_test_adapter import (
    DeterministicTestAdapter,
)


ENV_NAME = "DELIA_RESPONSE_INTELLIGENCE_ENABLED"

@pytest.fixture
def capture_mode_logs(caplog):
    """caplog cannot see app.* records once configure_logging has set
    propagate=False/WARNING on the "app" parent — the same pattern used
    by test_execution_ceiling_turn_budget's app_log_propagation."""
    app_logger = logging.getLogger("app")
    previous = (app_logger.propagate, app_logger.level)
    app_logger.propagate = True
    app_logger.setLevel(logging.INFO)
    try:
        with caplog.at_level(logging.INFO):
            yield caplog
    finally:
        app_logger.propagate, app_logger.level = previous


def _context() -> PlatformAccessContext:
    return PlatformAccessContext(
        user_id="u1",
        name="User",
        email="u@example.com",
        effective_permissions=("delia.access",),
        is_superadmin=False,
    )


def _outcome() -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="provider_alpha:guide",
            remote_name="get_guide",
            protocol=InteropProtocol.MCP,
            correlation_id="corr-1",
            observed_at="2026-01-01T00:00:00+00:00",
        ),
        content_text="raw owner text",
        structured={"items": [{"name": "Exemplo"}]},
    )


def _attempt() -> GovernedCapabilityAttempt:
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="corr-1",
        outcome=_outcome(),
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id="alpha",
                    source_system="fake_owner",
                    observed_at="2026-01-01T00:00:00+00:00",
                ),
            ),
            specialist_id="provider_alpha:guide",
            remote_capability="get_guide",
            action_id="get_guide",
            protocol="mcp",
            observed_at="2026-01-01T00:00:00+00:00",
            correlation_id="corr-1",
            is_complete=True,
            provider_id="provider_alpha",
            capability_group_id="provider_alpha:guide",
        ),
        content="Resultado governado de exemplo.",
    )


class _StubOrchestration:
    """Fixed governed-attempt producer — records call shape."""

    def __init__(self, attempt):
        self._attempt = attempt
        self.calls = []

    def attempt(self, input_text, **kwargs):
        self.calls.append((input_text, kwargs))
        return self._attempt


def _handler(enabled: bool, model=None, orchestration=None):
    return HandleInteractiveConversationTurn(
        InvokeModel(model or DeterministicTestAdapter()),
        capability_orchestration=orchestration,
        response_intelligence_enabled=enabled,
    )


def _turn(handler: HandleInteractiveConversationTurn):
    return handler.execute(
        InteractiveTurnRequest(
            access_context=_context(), input_text="liste os exemplos"
        )
    )


# ---------------------------------------------------------------------------
# A — configuration contract
# ---------------------------------------------------------------------------


def test_flag_defaults_off_when_absent(monkeypatch):
    monkeypatch.delenv(ENV_NAME, raising=False)
    s = Settings()
    assert s.response_intelligence_enabled is False
    assert s.response_intelligence_config_source == "default"
    assert s.response_intelligence_config_invalid is False


@pytest.mark.parametrize("value", ["1", "true", "yes", "on", "TRUE", " On "])
def test_flag_accepts_true_vocabulary(monkeypatch, value):
    monkeypatch.setenv(ENV_NAME, value)
    s = Settings()
    assert s.response_intelligence_enabled is True
    assert s.response_intelligence_config_source == "environment"
    assert s.response_intelligence_config_invalid is False


@pytest.mark.parametrize("value", ["0", "false", "no", "off", "FALSE"])
def test_flag_accepts_false_vocabulary(monkeypatch, value):
    monkeypatch.setenv(ENV_NAME, value)
    s = Settings()
    assert s.response_intelligence_enabled is False
    assert s.response_intelligence_config_invalid is False


def test_flag_invalid_value_fails_closed(monkeypatch):
    monkeypatch.setenv(ENV_NAME, "banana")
    s = Settings()
    assert s.response_intelligence_enabled is False
    assert s.response_intelligence_config_invalid is True
    assert s.response_intelligence_config_source == "environment"


def test_runtime_sha_unknown_when_unset(monkeypatch):
    monkeypatch.delenv("DELIA_RUNTIME_SHA", raising=False)
    s = Settings()
    assert s.runtime_sha == "unknown"


def test_runtime_sha_from_env(monkeypatch):
    monkeypatch.setenv("DELIA_RUNTIME_SHA", "abc123")
    assert Settings().runtime_sha == "abc123"


# ---------------------------------------------------------------------------
# Composition — single resolution point, typed injection
# ---------------------------------------------------------------------------


def _settings_with_flag(monkeypatch, value):
    monkeypatch.setenv(ENV_NAME, value)
    return Settings.for_testing()


def test_composer_injects_cri_mode(monkeypatch, capture_mode_logs):
    settings = _settings_with_flag(monkeypatch, "true")
    handler = _compose_turn_handler(
        InvokeModel(DeterministicTestAdapter()),
        DEFAULT_MODEL_REF,
        None,
        settings,
        {},
    )
    assert handler._response_mode == "cri"
    assert "mode=cri" in capture_mode_logs.text
    assert "config_source=environment" in capture_mode_logs.text
    assert "runtime_sha=" in capture_mode_logs.text


def test_composer_injects_baseline_mode(monkeypatch, capture_mode_logs):
    settings = _settings_with_flag(monkeypatch, "false")
    handler = _compose_turn_handler(
        InvokeModel(DeterministicTestAdapter()),
        DEFAULT_MODEL_REF,
        None,
        settings,
        {},
    )
    assert handler._response_mode == "baseline"
    assert "mode=baseline" in capture_mode_logs.text


def test_composer_invalid_env_fails_closed_with_warning(
    monkeypatch, capture_mode_logs
):
    settings = _settings_with_flag(monkeypatch, "banana")
    handler = _compose_turn_handler(
        InvokeModel(DeterministicTestAdapter()),
        DEFAULT_MODEL_REF,
        None,
        settings,
        {},
    )
    assert handler._response_mode == "baseline"
    assert "invalid_env_value" in capture_mode_logs.text


# ---------------------------------------------------------------------------
# B — OFF parity and C — ON selection at the response boundary
# ---------------------------------------------------------------------------


def _result_projection(result):
    wire = serialize_result(result)
    # Turn/session identities are per-run — compare semantic fields only.
    return {
        k: v
        for k, v in wire.items()
        if k not in {"session_id", "user_turn_id", "result_turn_id",
                     "generated_at"}
    }


def test_off_and_on_produce_identical_governed_results(
    capture_mode_logs,
):
    stub_off = _StubOrchestration(_attempt())
    stub_on = _StubOrchestration(_attempt())
    off = _result_projection(_turn(_handler(False, orchestration=stub_off)))
    on_result = _turn(_handler(True, orchestration=stub_on))
    on = _result_projection(on_result)
    # Functional equivalence — content, status, limitations, grounding,
    # provenance, message kind and presentation are identical.
    assert on == off
    # ON is observable at the boundary.
    assert "stage=response_mode decision=cri" in capture_mode_logs.text
    # The governed attempt received identical call shape (per-run
    # session/deadline identities excluded).
    identity = {"session_id", "turn_deadline"}
    shape_off = {
        k: v for k, v in stub_off.calls[0][1].items() if k not in identity
    }
    shape_on = {
        k: v for k, v in stub_on.calls[0][1].items() if k not in identity
    }
    assert stub_off.calls[0][0] == stub_on.calls[0][0]
    assert shape_off == shape_on


def test_baseline_mode_marker_logged(capture_mode_logs):
    _turn(_handler(False, orchestration=_StubOrchestration(_attempt())))
    assert (
        "stage=response_mode decision=baseline" in capture_mode_logs.text
    )


def test_on_performs_no_additional_model_calls():
    class SpyModel(DeterministicTestAdapter):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def invoke(self, request):
            self.calls += 1
            return super().invoke(request)

    model_off, model_on = SpyModel(), SpyModel()
    _turn(_handler(False, model=model_off,
                   orchestration=_StubOrchestration(_attempt())))
    _turn(_handler(True, model=model_on,
                   orchestration=_StubOrchestration(_attempt())))
    assert model_on.calls == model_off.calls


# ---------------------------------------------------------------------------
# D — security: the flag never widens authority
# ---------------------------------------------------------------------------


def test_flag_does_not_reach_orchestration_or_change_status():
    rejected = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.WRITE_REJECTED,
        correlation_id="corr-2",
        content="Escrita recusada pela governança.",
    )
    stub = _StubOrchestration(rejected)
    on = _turn(_handler(True, orchestration=stub))
    off = _turn(_handler(False, orchestration=_StubOrchestration(rejected)))
    assert on.content == off.content
    assert on.grounding_status == off.grounding_status
    assert on.message_kind == off.message_kind
    # Same attempt arguments in both modes — no flag leaked into the
    # governed path (selection, AuthZ, PREPARE/ACT untouched).
    assert stub.calls[0][0] == "liste os exemplos"


# ---------------------------------------------------------------------------
# E — rollback: env flip + composition rebuild restores baseline
# ---------------------------------------------------------------------------


def test_off_on_off_cycle_restores_baseline(monkeypatch):
    def mode_for(value):
        monkeypatch.setenv(ENV_NAME, value)
        handler = _compose_turn_handler(
            InvokeModel(DeterministicTestAdapter()),
            DEFAULT_MODEL_REF,
            None,
            Settings(),
            {},
        )
        return handler._response_mode

    assert mode_for("false") == "baseline"
    assert mode_for("true") == "cri"
    assert mode_for("false") == "baseline"
    monkeypatch.delenv(ENV_NAME, raising=False)
    handler = _compose_turn_handler(
        InvokeModel(DeterministicTestAdapter()),
        model_ref=None,
        interop=None,
        settings=Settings(),
        connections={},
    )
    assert handler._response_mode == "baseline"
