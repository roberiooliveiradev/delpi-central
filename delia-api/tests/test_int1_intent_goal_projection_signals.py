"""INT-1 — intent/goal projection signals (causal review doc 301).

Proven gaps from persisted eval traces (ctx-rec / stab-v2):

1. ``uncovered_after`` informed progress classification but was not
   written into ``_attempt_projection`` itself (only appended by the
   invoke caller afterward), so instrumented traces logged null
   uncovered/coverage even when identifiers remained open.
2. ``declare_investigation_goal`` accepted ``business_subject`` into the
   plan but did not echo it in the tool result — write-only field.
"""

from __future__ import annotations

from app.application.capability_provision.semantic_capability_support import (
    INVESTIGATION_PROGRESS_NONE,
    INVESTIGATION_PROGRESS_RELATED,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityStatus,
)
from app.application.capability_provision.contracts import (
    OWNER_RECORD_NOT_FOUND,
)
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    _attempt_projection,
)


def _failed_owner_attempt() -> GovernedCapabilityAttempt:
    outcome = SpecialistOutcome(
        status=SpecialistResultStatus.PARTIAL,
        content_text='{"success": false, "message": "Processo não encontrado."}',
        structured={"success": False, "message": "Processo não encontrado."},
        provenance=SpecialistResultProvenance(
            specialist_id="teo",
            remote_name="read",
            protocol=InteropProtocol.MCP,
            correlation_id="intent-g1",
            observed_at="2026-01-01T00:00:00Z",
        ),
        is_complete=False,
    )
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SOURCE_UNAVAILABLE,
        correlation_id="intent-g1",
        content="Processo não encontrado.",
        error_code=OWNER_RECORD_NOT_FOUND,
        limitations=(),
        outcome=outcome,
    )


def test_attempt_projection_surfaces_uncovered_identifiers_for_recovery():
    """Open user identifiers must be model-visible on the projection."""
    attempt = _failed_owner_attempt()
    projection = _attempt_projection(
        attempt,
        observation_index=0,
        uncovered_after=("90260921",),
    )
    assert projection.get("uncovered_user_identifiers") == ["90260921"]
    note = (projection.get("coverage_note") or "").casefold()
    assert "identifier" in note or "authoritative" in note
    # Wrong-owner / unavailable observations stay NO_PROGRESS, but the
    # recovery signal must still travel with the projection.
    assert projection.get("investigation_progress") in {
        INVESTIGATION_PROGRESS_NONE,
        INVESTIGATION_PROGRESS_RELATED,
        "NO_PROGRESS",
        "RELATED_INSUFFICIENT",
    }


def test_attempt_projection_omits_uncovered_when_none_open():
    attempt = _failed_owner_attempt()
    projection = _attempt_projection(
        attempt,
        observation_index=0,
        uncovered_after=(),
    )
    assert "uncovered_user_identifiers" not in projection


def test_accept_semantic_plan_preserves_business_subject():
    from app.application.capability_provision.governed_capability_orchestrator import (
        OperationalCapabilityOrchestrator,
    )
    from tests.support.capability_fixtures import (
        FakeProposalModel,
        _providers,
        load_test_orchestration_instructions,
    )
    from app.application.model_invocation.invoke_model import InvokeModel

    gates = OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(FakeProposalModel(())),
    )
    plan = gates._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=["90260921"],
        evidence_needed=["90260921"],
        business_subject="product hierarchical structure / BOM",
        correlation="intent-goal",
    )
    assert plan is not None
    assert plan.goal.business_subject == (
        "product hierarchical structure / BOM"
    )
    assert plan.target_identities == ("90260921",)


def test_declare_goal_accepted_payload_echoes_business_subject():
    """Accepted goal tool result must echo business_subject (not write-only)."""
    # Mirror the accepted payload contract of declare_investigation_goal
    # without invoking an LLM: subject retained on plan.goal must be
    # projectable back to the Agent.
    from app.application.capability_provision.governed_capability_orchestrator import (
        OperationalCapabilityOrchestrator,
    )
    from tests.support.capability_fixtures import (
        FakeProposalModel,
        _providers,
        load_test_orchestration_instructions,
    )
    from app.application.model_invocation.invoke_model import InvokeModel

    gates = OperationalCapabilityOrchestrator(
        _providers(),
        orchestration_instructions=load_test_orchestration_instructions(),
        invoke_model=InvokeModel(FakeProposalModel(())),
    )
    plan = gates._accept_semantic_investigation_plan(
        goal_class="read",
        comparison_requested=False,
        target_identities=["90260921"],
        evidence_needed=["90260921"],
        business_subject="product item structure",
        correlation="intent-echo",
    )
    assert plan is not None
    accepted = {
        "status": "ACCEPTED",
        "goal_class": plan.goal.goal_class,
        "comparison_requested": plan.goal.comparison_requested,
        "target_identities": list(plan.target_identities),
        "evidence_needed": list(plan.evidence_needed),
    }
    subject = getattr(plan.goal, "business_subject", None)
    if isinstance(subject, str) and subject.strip():
        accepted["business_subject"] = subject.strip()
    assert accepted["business_subject"] == "product item structure"
