"""Doc 231 — Pydantic AI investigation runtime characterization."""

from __future__ import annotations

from app.application.capability_provision.orchestration import (
    OperationalCapabilityOrchestrator,
)
from app.application.interaction.capability_attempt import (
    EARLY_CONVERSATIONAL_ADMISSION,
    GovernedCapabilityStatus,
)
from app.application.model_invocation.invoke_model import InvokeModel
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    PydanticAiInvestigationOrchestrator,
)
from pydantic_ai.models.test import TestModel
from tests.test_engine_b_recovery_reuse import _providers, _reuse_proposal
from tests.test_goal_evidence_relevance import (
    FakeProposalModel as RelevanceProposalModel,
)
from tests.test_governed_attempt_contract import (
    _cri_clause,
    load_test_orchestration_instructions,
)


def _gates(proposal=None):
    clause = _cri_clause()
    return OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(
            RelevanceProposalModel(proposal or _reuse_proposal())
        ),
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )


def test_conversational_admission_skips_agent_tools():
    """Admission class explanation → NOT_APPLICABLE without tools."""
    from datetime import datetime, timezone

    from app.application.model_invocation.contracts import (
        ProviderInvocationPayload,
    )
    from app.domain.model_invocation.model import (
        InvocationFinishStatus,
        ProviderExposureClass,
    )

    class _AdmissionOnlyModel:
        adapter_kind = "TEST_ONLY"
        exposure_class = ProviderExposureClass.TEST_ONLY

        def invoke(self, request):
            purpose = getattr(request, "task_purpose_id", "") or ""
            if purpose.endswith("interaction_admission"):
                payload = {
                    "requires_owner_surface": False,
                    "interaction_class": "explanation",
                }
            else:
                payload = {"applicable": False}
            return ProviderInvocationPayload(
                structured_output=payload,
                generated_at=datetime.now(timezone.utc).isoformat(),
                finish_status=InvocationFinishStatus.COMPLETED,
            )

    from tests.test_governed_attempt_contract import TEST_MODEL_REF

    clause = _cri_clause()
    gates = OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(_AdmissionOnlyModel()),
        model_ref=TEST_MODEL_REF,
        response_intelligence_enabled=True,
        cri_instruction_clause=clause.text,
        cri_instruction_version=clause.version,
    )
    engine = PydanticAiInvestigationOrchestrator(
        gates, model=TestModel(call_tools=[])
    )
    attempt = engine.attempt("O que é SIPOC?")
    assert attempt.status is GovernedCapabilityStatus.NOT_APPLICABLE
    assert attempt.admission_outcome == EARLY_CONVERSATIONAL_ADMISSION
    assert "admission" in engine.last_node_trace
    assert "conversational" in engine.last_node_trace
    assert "investigation" not in engine.last_node_trace


def test_no_langgraph_import_in_investigation_module():
    from pathlib import Path
    import re

    src = Path(
        "app/infrastructure/orchestration/pydantic_ai_investigation.py"
    ).read_text(encoding="utf-8")
    assert not re.search(r"\blanggraph\b", src)


def test_project_semantic_tool_catalog_omits_writes():
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c-test",
        deadline=__import__(
            "app.application.interaction.turn_budget", fromlist=["TurnDeadline"]
        ).TurnDeadline.start(30.0),
    )
    assert isinstance(catalog, list)
    for entry in catalog:
        assert entry["operation_class"] in {
            "READ",
            "DISCOVERY",
            "ANALYSIS",
        }
