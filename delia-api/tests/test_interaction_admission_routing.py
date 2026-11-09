"""R01 — behavioral routing for interaction admission.

Exercises the existing ``_admit_conversational_turn`` decision
boundary and the investigation engine's branch that either starts
the MCP Agent or stays conversational. Fake proposals isolate the
routing contract from model variance; live Qwen/Kimi evals cover
admission accuracy separately.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.application.capability_provision.governed_capability_orchestrator import (
    OperationalCapabilityOrchestrator,
)
from app.application.capability_provision.semantic_capability_support import (
    INTERACTION_ADMISSION_INSTRUCTION_ID,
)
from app.application.interaction.capability_attempt import (
    EARLY_CONVERSATIONAL_ADMISSION,
    SURFACE_INQUIRY_ADMISSION,
    GovernedCapabilityStatus,
)
from app.application.interaction.turn_budget import TurnDeadline
from app.application.model_invocation.contracts import (
    ConversationContextTurn,
    ProviderInvocationPayload,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.domain.interaction.model import TurnKind
from app.domain.model_invocation.model import (
    InvocationFinishStatus,
    ProviderExposureClass,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    PydanticAiInvestigationOrchestrator,
)
from pydantic_ai.models.test import TestModel
from tests.support.capability_fixtures import (
    TEST_MODEL_REF,
    FakeProposalModel,
    _providers,
    load_test_orchestration_instructions,
)


def _payload(requires: bool | str | None, interaction_class: str | None):
    body: dict = {}
    if requires is not None:
        body["requires_owner_surface"] = requires
    if interaction_class is not None:
        body["interaction_class"] = interaction_class
    return body


def _gates_with_admission(*proposals: dict):
    queued = [
        {INTERACTION_ADMISSION_INSTRUCTION_ID: proposal}
        for proposal in proposals
    ]
    return OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(FakeProposalModel(queued)),
        model_ref=TEST_MODEL_REF,
    )


def _admit(gates, text: str = "processos na engenharia", prior=()):
    return gates._admit_conversational_turn(
        text,
        workspace_context=None,
        prior_turns=tuple(prior),
        correlation="adm-test",
        deadline=TurnDeadline.start(30.0),
    )


def test_t01_operational_admission_routes_to_owner_path():
    gates = _gates_with_admission(
        _payload(True, "operational"),
    )
    interaction_class, owner_required = _admit(gates)
    assert owner_required is True
    assert interaction_class is None


def test_t02_conceptual_explanation_stays_conversational():
    gates = _gates_with_admission(
        _payload(False, "explanation"),
    )
    interaction_class, owner_required = _admit(
        gates, text="O que é SIPOC?"
    )
    assert owner_required is False
    assert interaction_class == "explanation"

    engine = PydanticAiInvestigationOrchestrator(
        gates, model=TestModel(call_tools=[])
    )
    # Re-queue via a fresh gates instance for the engine path.
    gates2 = _gates_with_admission(_payload(False, "explanation"))
    engine = PydanticAiInvestigationOrchestrator(
        gates2, model=TestModel(call_tools=[])
    )
    attempt = engine.attempt("O que é SIPOC?")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert attempt.admission_outcome == EARLY_CONVERSATIONAL_ADMISSION
    assert "investigation" not in engine.last_node_trace
    assert "conversational" in engine.last_node_trace


def test_t03_ambiguous_admission_preserves_owner_path():
    gates = _gates_with_admission(_payload(True, "ambiguous"))
    interaction_class, owner_required = _admit(
        gates, text="melhoria na engenharia"
    )
    assert owner_required is True
    assert interaction_class is None


def test_t04_contradictory_pairs_fail_closed_to_owner_when_operational():
    # requires=false but class=operational → owner path (existing gate).
    gates = _gates_with_admission(_payload(False, "operational"))
    interaction_class, owner_required = _admit(gates)
    assert owner_required is True
    assert interaction_class is None

    # requires=true but class=explanation → owner path (requires wins).
    gates = _gates_with_admission(_payload(True, "explanation"))
    interaction_class, owner_required = _admit(gates)
    assert owner_required is True
    assert interaction_class is None


def test_t05_multiturn_current_message_decides_routing():
    prior = (
        ConversationContextTurn(
            kind=TurnKind.USER_INPUT, content="O que é SIPOC?"
        ),
        ConversationContextTurn(
            kind=TurnKind.DELIA_RESULT,
            content="SIPOC e um mapa de processo.",
        ),
    )
    # Current turn operational despite conceptual history.
    gates = _gates_with_admission(_payload(True, "operational"))
    _, owner_required = _admit(
        gates, text="Quais iniciativas estão registradas?", prior=prior
    )
    assert owner_required is True

    # Topic change to conceptual → conversational.
    gates = _gates_with_admission(_payload(False, "explanation"))
    interaction_class, owner_required = _admit(
        gates, text="Explique o conceito de melhoria continua.", prior=prior
    )
    assert owner_required is False
    assert interaction_class == "explanation"


def test_t06_surface_inquiry_requires_coherent_confirmation():
    # Two coherent surface_inquiry + requires=false → surface path.
    gates = _gates_with_admission(
        _payload(False, "surface_inquiry"),
        _payload(False, "surface_inquiry"),
    )
    interaction_class, owner_required = _admit(
        gates, text="O que voce pode consultar?"
    )
    assert interaction_class == "surface_inquiry"
    assert owner_required is True  # surface listing consulted

    engine = PydanticAiInvestigationOrchestrator(
        _gates_with_admission(
            _payload(False, "surface_inquiry"),
            _payload(False, "surface_inquiry"),
        ),
        model=TestModel(call_tools=[]),
    )
    attempt = engine.attempt("O que voce pode consultar?")
    assert attempt.admission_outcome == SURFACE_INQUIRY_ADMISSION
    assert "investigation" not in engine.last_node_trace

    # Contradiction on confirm → fail-closed owner path.
    gates = _gates_with_admission(
        _payload(False, "surface_inquiry"),
        _payload(True, "operational"),
    )
    interaction_class, owner_required = _admit(
        gates, text="O que voce pode consultar?"
    )
    assert interaction_class is None
    assert owner_required is True


def test_t01_engine_starts_investigation_when_owner_required():
    """Owner-required admission must enter the investigation node
    (MCP Agent path), not the early conversational skip."""

    class _AdmissionThenBusy:
        adapter_kind = "TEST_ONLY"
        exposure_class = ProviderExposureClass.TEST_ONLY
        calls = 0

        def invoke(self, request):
            self.calls += 1
            purpose = getattr(request, "task_purpose_id", "") or ""
            if purpose.endswith("interaction_admission"):
                payload = {
                    "requires_owner_surface": True,
                    "interaction_class": "operational",
                }
            else:
                payload = {"applicable": False}
            return ProviderInvocationPayload(
                structured_output=payload,
                generated_at=datetime.now(timezone.utc).isoformat(),
                finish_status=InvocationFinishStatus.COMPLETED,
            )

    model_port = _AdmissionThenBusy()
    gates = OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(model_port),
        model_ref=TEST_MODEL_REF,
    )
    engine = PydanticAiInvestigationOrchestrator(
        gates, model=TestModel(call_tools=[])
    )
    attempt = engine.attempt("processos na engenharia")
    assert "admission" in engine.last_node_trace
    assert "investigation" in engine.last_node_trace
    assert "conversational" not in engine.last_node_trace
    assert attempt.admission_outcome != EARLY_CONVERSATIONAL_ADMISSION


def test_instruction_resource_is_v42_with_object_test():
    """Contract lock: admission instruction carries the object-first
    remediation without freezing example phrases as runtime rules."""
    instructions = load_test_orchestration_instructions()
    text = instructions[INTERACTION_ADMISSION_INSTRUCTION_ID]
    assert "Classify by OBJECT" in text
    assert "TRUE by default" in text
    assert "never explanation" in text
    assert "definitional ask" in text
    assert "processos na engenharia" not in text
