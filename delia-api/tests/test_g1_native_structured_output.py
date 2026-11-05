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
    # mixed valid/invalid refs + plan=None → COMPLETE never honored;
    # verified deterministic content is always the authoritative answer
    assert out.content == "deterministic content"
    assert "declared_status_overridden" in out.limitations


def test_valid_sourceref_never_promotes_hallucinated_prose():
    """A valid indexed SourceRef proves the observation's provenance —
    never the truth of generated prose. Model wording must not replace
    the verified deterministic answer (doc 258 §1)."""
    terminal = _terminal()
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="the product costs R$ 999,90 and ships tomorrow",
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(_attempt(),),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert "999" not in (out.content or "")
    assert out.content == "deterministic content"


def test_real_but_irrelevant_evidence_does_not_ground_complete():
    """Real observation exists but coverage is unknown (plan=None) —
    a COMPLETE claim can never be proven vacuously (doc 258 §4)."""
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="anything",
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
    assert "declared_status_overridden" in out.limitations
    assert "coverage_unknown" in out.limitations
    assert out.content == "deterministic content"


def test_complete_proven_only_when_all_refs_bind_and_obligations_met():
    """Fully consistent COMPLETE (all refs valid, obligations satisfied)
    is accepted as consistent — but STILL never replaces the verified
    deterministic content (doc 258 §1)."""
    class _Plan:
        evidence_needed = ()

    terminal = _terminal()
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="model wording",
        evidence_refs=(0,),
    )
    out = _apply_declared_answer(
        terminal=terminal,
        declared_answer=declared,
        collected=(_attempt(),),
        plan=_Plan(),
        correlation="c1",
        unbound_outcome=None,
    )
    # coverage_unknown (evidence_needed empty) — or consistent; either
    # way the deterministic content stays authoritative
    assert out.content == "deterministic content"


def test_unknown_schema_version_rejects_whole_declaration():
    declared = InvestigationAnswer(
        schema_version="2",
        status=InvestigationAnswerStatus.COMPLETE,
        answer="x",
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
    assert "declared_schema_rejected" in out.limitations
    assert out.content == "deterministic content"


def test_clarification_never_discards_verified_answer():
    """Model-declared clarification must not throw away a terminal that
    already carries verified business evidence (doc 258 §5)."""
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.NEEDS_CLARIFICATION,
        clarification_question="Qual registro?",
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(_attempt(),),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.SUCCESS
    assert "declared_clarification_ignored" in out.limitations


def test_clarification_still_applies_when_no_verified_evidence():
    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.NEEDS_CLARIFICATION,
        clarification_question="Qual registro consultar?",
    )
    empty_terminal = GovernedCapabilityAttempt(
        status=GovernedCapabilityStatus.NOT_APPLICABLE,
        correlation_id="c1",
        limitations=("insufficient_evidence",),
    )
    out = _apply_declared_answer(
        terminal=empty_terminal,
        declared_answer=declared,
        collected=(),
        plan=None,
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED


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


# ------------------------------------------------------------------
# residual G1 (doc 259 §25): clarification with PARTIAL evidence
# ------------------------------------------------------------------


def test_clarification_applies_with_partial_evidence_and_unmet_obligations():
    """Verified partial evidence coexisting with unmet material
    obligations must NOT cause a declared clarification to be dropped —
    the bounded clarification path applies while the verified evidence
    is preserved, never discarded."""
    class _Plan:
        evidence_needed = ("price_check", "stock_check")

    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.NEEDS_CLARIFICATION,
        clarification_question="Qual armazém consultar para o estoque?",
    )
    # terminal carries REAL verified owner evidence (outcome+provenance)
    verified_terminal = dataclasses.replace(
        _terminal(),
        outcome=_outcome(),
        provenance=_attempt().provenance,
    )
    out = _apply_declared_answer(
        terminal=verified_terminal,
        declared_answer=declared,
        collected=(_attempt(),),
        plan=_Plan(),
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.CLARIFICATION_REQUIRED
    # verified evidence preserved — real fields survive the
    # clarification, not merely the marker
    assert "verified_evidence_preserved" in out.limitations
    assert out.outcome is verified_terminal.outcome
    assert out.provenance is verified_terminal.provenance
    assert out.provenance.source_refs[0].source_id == "pa"


def test_clarification_ignored_only_when_obligations_fully_met():
    """When material obligations are all satisfied, a declared
    clarification is ignored — there is no proven unmet need."""
    class _Plan:
        evidence_needed = ()

    declared = InvestigationAnswer(
        schema_version="1",
        status=InvestigationAnswerStatus.NEEDS_CLARIFICATION,
        clarification_question="Qual registro?",
    )
    out = _apply_declared_answer(
        terminal=_terminal(),
        declared_answer=declared,
        collected=(_attempt(),),
        plan=_Plan(),
        correlation="c1",
        unbound_outcome=None,
    )
    assert out.status is GovernedCapabilityStatus.SUCCESS
    assert "declared_clarification_ignored" in out.limitations
