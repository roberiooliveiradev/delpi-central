"""Early conversational admission uses the remaining global budget.

Post-orchestration NOT_APPLICABLE keeps the 12s fallback cap.
The global 30s deadline is never restarted.
"""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    GROUP_SELECTION_INSTRUCTION_ID,
    INTERACTION_ADMISSION_INSTRUCTION_ID,
)
from app.application.interaction.capability_attempt import (
    EARLY_CONVERSATIONAL_ADMISSION,
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.interaction.contracts import InteractiveTurnRequest
from app.application.interaction.handle_interactive_turn import (
    CONVERSATIONAL_BUDGET_MESSAGE,
    CONVERSATIONAL_FALLBACK_STAGE_CAP_SECONDS,
    DELPI_SOURCE_DENIED_MESSAGE,
    DELPI_SOURCE_UNAVAILABLE_MESSAGE,
    HandleInteractiveConversationTurn,
)
from app.application.model_invocation.errors import TIMEOUT, ModelInvocationError
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.evidence.model import EpistemicClass
from app.domain.interaction.model import GroundingStatus
from app.domain.model_invocation.model import ProviderExposureClass
from tests.test_interaction_runtime import _context
from tests.test_specialist_capability_orchestration import (
    FakePort,
    TEO_TOOLS,
    VISTA_TOOLS,
    _interop,
    _read,
)


class _SpyModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self, answer: str = "SIPOC é um mapa conceitual."):
        self.requests = []
        self._answer = answer

    def invoke(self, request):
        from app.application.model_invocation.contracts import (
            ProviderInvocationPayload,
        )

        self.requests.append(request)
        return ProviderInvocationPayload(
            structured_output={"answer": self._answer},
            generated_at="2026-01-01T00:00:00+00:00",
        )


class _TimeoutModel:
    adapter_kind = "TEST_ONLY"
    exposure_class = ProviderExposureClass.TEST_ONLY

    def __init__(self):
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        raise ModelInvocationError(TIMEOUT, "stage timed out")


class _FixedOrchestration:
    def __init__(self, attempt):
        self._attempt = attempt
        self.calls = 0

    def attempt(self, *args, **kwargs):
        self.calls += 1
        return self._attempt


def _run(attempt, model, budget=30.0):
    handler = HandleInteractiveConversationTurn(
        InvokeModel(model),
        capability_orchestration=_FixedOrchestration(attempt),
        turn_budget_seconds=budget,
    )
    result = handler.execute(
        InteractiveTurnRequest(
            access_context=_context(),
            input_text="O que é SIPOC?",
            command_type="MESSAGE",
        )
    )
    return result


def test_t01_early_admission_is_not_capped_at_12s():
    model = _SpyModel()
    result = _run(
        GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id="c",
            admission_outcome=EARLY_CONVERSATIONAL_ADMISSION,
        ),
        model,
    )
    assert model.requests
    timeout = model.requests[0].timeout_seconds
    assert timeout > CONVERSATIONAL_FALLBACK_STAGE_CAP_SECONDS
    assert timeout <= 30.0
    assert "SIPOC" in result.content
    assert result.grounding_status is GroundingStatus.NON_GROUNDED


def test_t02_post_orchestration_not_applicable_keeps_12s_cap():
    model = _SpyModel()
    _run(
        GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id="c",
        ),
        model,
    )
    assert model.requests[0].timeout_seconds <= (
        CONVERSATIONAL_FALLBACK_STAGE_CAP_SECONDS + 0.01
    )


def test_t03_early_admission_stays_inside_global_budget():
    model = _SpyModel()
    _run(
        GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id="c",
            admission_outcome=EARLY_CONVERSATIONAL_ADMISSION,
        ),
        model,
        budget=8.0,
    )
    timeout = model.requests[0].timeout_seconds
    assert timeout <= 8.0
    assert timeout < CONVERSATIONAL_FALLBACK_STAGE_CAP_SECONDS + 4


def test_t04_owner_error_does_not_invoke_free_form_model():
    model = _SpyModel("fato inventado da DELPI")
    result = _run(
        GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
            correlation_id="c",
            error_code="openapi_invocation_failed",
        ),
        model,
    )
    assert model.requests == []
    assert result.content == DELPI_SOURCE_UNAVAILABLE_MESSAGE
    assert result.grounding_status is GroundingStatus.NON_GROUNDED


def test_t05_model_timeout_does_not_invent_business_data():
    model = _TimeoutModel()
    result = _run(
        GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.NOT_APPLICABLE,
            correlation_id="c",
            admission_outcome=EARLY_CONVERSATIONAL_ADMISSION,
        ),
        model,
    )
    assert result.content == CONVERSATIONAL_BUDGET_MESSAGE
    assert result.epistemic_class is EpistemicClass.HYPOTHESIS
    assert result.grounding_status is GroundingStatus.NON_GROUNDED
    assert "DELPI" not in result.content or "não inventei" in result.content


def test_t06_authz_and_confirmation_do_not_open_conversational_act():
    denied_model = _SpyModel()
    denied = _run(
        GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.AUTHZ_DENIED,
            correlation_id="c",
        ),
        denied_model,
    )
    assert denied_model.requests == []
    assert denied.content == DELPI_SOURCE_DENIED_MESSAGE

    confirm_model = _SpyModel()
    confirmed = _run(
        GovernedCapabilityAttempt(
            status=GovernedCapabilityStatus.CONFIRMATION_REQUIRED,
            correlation_id="c",
            content="Aguardando confirmação para preparar a alteração.",
        ),
        confirm_model,
    )
    assert confirm_model.requests == []
    assert confirmed.message_kind == "CONFIRMATION_REQUIRED"


def test_orchestrator_marks_only_typed_early_admission():
    port = FakePort(
        tools_by_specialist={"teo": TEO_TOOLS, "vista": VISTA_TOOLS}
    )
    early = _read(
        _interop(port),
        specialist_ids=("teo", "vista"),
        proposal={
            INTERACTION_ADMISSION_INSTRUCTION_ID: {
                "requires_owner_surface": False,
                "interaction_class": "explanation",
            }
        },
    ).attempt("O que é SIPOC?")
    assert early.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert early.admission_outcome == EARLY_CONVERSATIONAL_ADMISSION
    assert port.list_calls == []

    later_port = FakePort(
        tools_by_specialist={"teo": TEO_TOOLS, "vista": VISTA_TOOLS}
    )
    later = _read(
        _interop(later_port),
        specialist_ids=("teo", "vista"),
        proposal={
            INTERACTION_ADMISSION_INSTRUCTION_ID: {
                "requires_owner_surface": True,
                "interaction_class": "operational",
            },
            GROUP_SELECTION_INSTRUCTION_ID: {"applicable": False},
        },
    ).attempt("Quais formatos de dados estão disponíveis?")
    assert later.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert later.admission_outcome is None
    assert later_port.list_calls
