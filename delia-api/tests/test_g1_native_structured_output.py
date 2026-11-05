"""G1 — native typed structured output for the investigation Agent.

The Agent declares an ``InvestigationAnswer`` (strict dataclass) via
``output_type``; the deterministic acceptor
``_apply_declared_answer`` binds every claim to real collected
attempts — refs that do not point to actual business evidence are
dropped, a COMPLETE claim is honored only when obligations are
satisfied, and nothing the model declares becomes authority or FACT.
"""

from __future__ import annotations

import dataclasses

from app.application.capability_provision.contracts import (
    InvestigationAnswer,
    InvestigationAnswerStatus,
)
from app.application.capability_provision.orchestration import (
    _apply_declared_answer,
)
from app.application.interaction.capability_attempt import (
    GovernedCapabilityAttempt,
    GovernedCapabilityProvenance,
    GovernedCapabilityStatus,
    SourceRef,
)
from app.domain.specialist_interop.model import (
    InteropProtocol,
    SpecialistOutcome,
    SpecialistResultProvenance,
    SpecialistResultStatus,
)


def _outcome() -> SpecialistOutcome:
    return SpecialistOutcome(
        status=SpecialistResultStatus.COMPLETED,
        provenance=SpecialistResultProvenance(
            specialist_id="pa",
            remote_name="search_items",
            protocol=InteropProtocol.MCP,
            correlation_id="c1",
            observed_at="2026-01-01T00:00:00Z",
        ),
        content_text="owner record",
        is_complete=True,
        structured={"items": [{"id": "1"}]},
    )


def _attempt(limitations: tuple[str, ...] = ()) -> GovernedCapabilityAttempt:
    outcome = _outcome()
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c1",
        outcome=outcome,
        provenance=GovernedCapabilityProvenance(
            source_refs=(
                SourceRef(
                    source_id="pa",
                    source_system="pa",
                    provider_name="pa",
                    observed_at="2026-01-01T00:00:00Z",
                ),
            ),
            specialist_id="pa",
            remote_capability="search_items",
            action_id="search_items",
            protocol=InteropProtocol.MCP.value,
            observed_at="2026-01-01T00:00:00Z",
            correlation_id="c1",
            is_complete=True,
        ),
        content="rendered",
        limitations=limitations,
    )


def _terminal() -> GovernedCapabilityAttempt:
    return GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.SUCCESS,
        correlation_id="c1",
        content="deterministic content",
        limitations=(),
    )


# ------------------------------------------------------------------
# contract
# ------------------------------------------------------------------


def test_investigation_answer_is_typed_not_permissive():
    answer = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="the record exists",
        evidence_refs=(0,),
    )
    assert answer.schema_version == "1"
    assert answer.status is InvestigationAnswerStatus.COMPLETE
    assert answer.evidence_refs == (0,)
    # no permissive dict payload — strict fields only
    assert dataclasses.is_dataclass(answer)
    assert not hasattr(answer, "extra")


# ------------------------------------------------------------------
# acceptor — fabricated refs never bind
# ------------------------------------------------------------------


def test_out_of_range_evidence_ref_is_dropped():
    terminal = _terminal()
    collected = (_attempt(),)
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="synthesized",
        evidence_refs=(0, 7),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=collected,
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert "evidence_ref_unbound:7" in out.limitations
    # complete claim honored for the one valid ref (no obligations)
    assert out.content == "synthesized"


def test_ref_to_non_business_attempt_is_dropped():
    non_business = _attempt(limitations=("discovery_metadata_observation",))
    terminal = _terminal()
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="synthesized",
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(non_business,),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert "evidence_ref_unbound:0" in out.limitations
    # unproven COMPLETE → deterministic content stays + override noted
    assert out.content == "deterministic content"
    assert "declared_status_overridden" in out.limitations


def test_complete_claim_without_any_valid_refs_is_overridden():
    terminal = _terminal()
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="synthesized",
        evidence_refs=(),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.content == "deterministic content"
    assert "declared_status_overridden" in out.limitations


# ------------------------------------------------------------------
# acceptor — clarification, partial, declared limitations
# ------------------------------------------------------------------


def test_declared_clarification_takes_bounded_path():
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.NEEDS_CLARIFICATION,
        clarification_question="Qual registro consultar?",
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    assert out.content == "Qual registro consultar?"
    assert "agent_requested_clarification" in out.limitations


def test_declared_unmet_obligations_merge_into_limitations():
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.PARTIAL,
        unmet_obligations=("price_check",),
        limitations=("owner_timeout",),
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert "declared_unmet_obligation:price_check" in out.limitations
    assert "declared_limitation:owner_timeout" in out.limitations


def test_no_declared_answer_passes_terminal_through():
    terminal = _terminal()
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=None,
        collected=(),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert out is terminal


def test_answer_text_is_bounded():
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="x" * 5000,
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(_attempt(),),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert len(out.content) <= 2000
