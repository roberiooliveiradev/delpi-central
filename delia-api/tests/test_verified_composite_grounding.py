"""E4-R6: bounded composite evidence is not a synthetic specialist result."""
from __future__ import annotations

import pytest

from app.application.capability_provision.governed_capability_orchestrator import (
    OperationalCapabilityOrchestrator,
)
from app.application.capability_provision.semantic_capability_support import (
    _verify_evidence_composition,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt, GovernedCapabilityStatus,
)
from app.application.interaction.contracts import VerifiedCompositeEvidence
from app.application.interaction.handle_interactive_turn import (
    HandleInteractiveConversationTurn, serialize_result,
)
from app.domain.evidence.model import EpistemicClass, SourceRef
from app.domain.interaction.model import (
    GroundingStatus, InteractionSession, InteractionTurn, TurnKind,
)


def _proof():
    return VerifiedCompositeEvidence(
        source_roots=("90260147", "90260148"),
        source_lineage=(
            (SourceRef("materials-left", "domain-materials"),),
            (SourceRef("materials-right", "domain-materials"),),
        ),
        observed_at="2026-11-04T10:00:00Z",
        correlation_id="comparison-1",
        verdict="differences_found",
    )


def _session():
    session = InteractionSession(
        session_id="session-1", started_at="2026-11-04T09:00:00Z"
    )
    turn = InteractionTurn(
        turn_id="user-1", session_id=session.session_id,
        kind=TurnKind.USER_INPUT, content="Compare as duas",
        occurred_at="2026-11-04T09:01:00Z",
    )
    return session, turn


def test_two_real_sources_project_without_synthetic_specialist():
    proof = _proof()
    p = proof.to_projection()
    assert [s["root_id"] for s in p["sources"]] == [
        "90260147", "90260148",
    ]
    assert p["specialist_id"] is None
    assert p["remote_capability"] is None
    assert proof.verdict == "differences_found"


def test_duplicate_root_and_missing_owner_lineage_rejected():
    with pytest.raises(ValueError):
        VerifiedCompositeEvidence(
            ("90260147", "90260147"),
            ((SourceRef("a", "erp"),), (SourceRef("b", "erp"),)),
            "2026-11-04T10:00:00Z", "c", "differences_found",
        )
    with pytest.raises(ValueError):
        VerifiedCompositeEvidence(
            ("90260147", "90260148"),
            ((), (SourceRef("b", "erp"),)),
            "2026-11-04T10:00:00Z", "c", "differences_found",
        )


def test_verified_composite_is_grounded_without_fake_owner_outcome():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="comparison-1",
        content="Comparação determinística das duas estruturas.",
        verified_composition=_proof(),
    )
    handler = object.__new__(HandleInteractiveConversationTurn)
    session, user_turn = _session()
    result = handler._grounded_composite_result(session, user_turn, attempt)
    p = serialize_result(result)
    assert result.epistemic_class is EpistemicClass.OBSERVATION
    assert p["grounding_status"] == GroundingStatus.GROUNDED.value
    assert p["provenance"]["composition"]["source_roots"] == [
        "90260147", "90260148",
    ]
    assert p["provenance"]["specialist_id"] is None


def test_plain_success_without_evidence_remains_non_grounded():
    attempt = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="context-only", content="Texto anterior.",
    )
    handler = object.__new__(HandleInteractiveConversationTurn)
    session, turn = _session()
    result = handler._prior_continuation_result(session, turn, attempt)
    assert result.grounding_status is GroundingStatus.NON_GROUNDED


def test_verifier_refuses_three_sources_instead_of_comparing_first_two():
    row = [{"code": "root", "description": "root", "quantity": 1, "unit": "PC", "path": ()}]
    result = _verify_evidence_composition(
        {"A": row, "B": row, "C": row}, None
    )
    assert result["verdict"] == "inconclusive"
