"""C3-T7 deterministic decision-path foundation tests.

All cases are deterministic; no model invocation occurs in any case.
NOT_EVERY_EVENT_CALLS_LLM = TRUE.
"""

from __future__ import annotations

import pytest

from app.domain.decision_path.model import (
    DecisionPath,
    DecisionPathInput,
    DecisionPathResult,
    DecisionPathStatus,
    RoutingReasonCode,
)
from app.domain.decision_path.rules import select_decision_path
from app.domain.evidence.model import EvidenceRef, SourceRef


def _facts(**overrides):
    facts = {
        "authoritative_deterministic_rule_available": False,
        "authoritative_context_sufficient": False,
        "structured_context_sufficient": False,
        "complex_investigation_required": False,
        "required_evidence_missing": False,
        "evidence_conflict_present": False,
    }
    facts.update(overrides)
    return facts


def _input(**overrides) -> DecisionPathInput:
    return DecisionPathInput(request_class="governed.readiness.check", **_facts(**overrides))


def test_decision_path_values_are_exact():
    assert {item.value for item in DecisionPath} == {
        "FAST",
        "OPERATIONAL",
        "REASONING",
    }


def test_same_input_produces_same_path():
    first = select_decision_path(
        _input(
            authoritative_deterministic_rule_available=True,
            authoritative_context_sufficient=True,
        )
    )
    second = select_decision_path(
        _input(
            authoritative_deterministic_rule_available=True,
            authoritative_context_sufficient=True,
        )
    )
    assert first == second
    assert first.selected_path is DecisionPath.FAST


def test_fast_selected_when_authoritative_rule_applies():
    result = select_decision_path(
        _input(
            authoritative_deterministic_rule_available=True,
            authoritative_context_sufficient=True,
        )
    )
    assert result.status is DecisionPathStatus.SELECTED
    assert result.selected_path is DecisionPath.FAST
    assert result.reason_codes == (RoutingReasonCode.AUTHORITATIVE_RULE_APPLIES,)


def test_operational_selected_for_bounded_structured_case_without_model():
    result = select_decision_path(_input(structured_context_sufficient=True))
    assert result.status is DecisionPathStatus.SELECTED
    assert result.selected_path is DecisionPath.OPERATIONAL
    assert result.invokes_model() is False


def test_reasoning_selected_for_complex_investigation_only():
    result = select_decision_path(_input(complex_investigation_required=True))
    assert result.status is DecisionPathStatus.SELECTED
    assert result.selected_path is DecisionPath.REASONING
    assert result.invokes_model() is False


def test_simple_deterministic_case_does_not_select_reasoning():
    result = select_decision_path(
        _input(
            authoritative_deterministic_rule_available=True,
            authoritative_context_sufficient=True,
        )
    )
    assert result.selected_path is not DecisionPath.REASONING


def test_authoritative_rule_priority_over_complex_investigation_flag():
    result = select_decision_path(
        _input(
            authoritative_deterministic_rule_available=True,
            authoritative_context_sufficient=True,
            complex_investigation_required=True,
        )
    )
    assert result.selected_path is DecisionPath.FAST


def test_rule_without_sufficient_context_is_not_fast():
    result = select_decision_path(
        _input(
            authoritative_deterministic_rule_available=True,
            structured_context_sufficient=True,
        )
    )
    assert result.selected_path is DecisionPath.OPERATIONAL


def test_missing_routing_facts_fail_closed():
    result = select_decision_path(
        DecisionPathInput(request_class="unknown.request")
    )
    assert result.status is DecisionPathStatus.INCONCLUSIVE
    assert result.selected_path is None
    assert result.reason_codes == (RoutingReasonCode.MISSING_ROUTING_FACTS,)


@pytest.mark.parametrize("fact", _facts().keys())
def test_each_missing_fact_fails_closed(fact):
    facts = _facts()
    facts[fact] = None
    result = select_decision_path(
        DecisionPathInput(request_class="any.request", **facts)
    )
    assert result.status is DecisionPathStatus.INCONCLUSIVE
    assert result.selected_path is None


def test_required_evidence_missing_blocks_routing():
    result = select_decision_path(
        _input(
            authoritative_deterministic_rule_available=True,
            authoritative_context_sufficient=True,
            required_evidence_missing=True,
        )
    )
    assert result.status is DecisionPathStatus.BLOCKED
    assert result.selected_path is None
    assert result.missing_evidence is True
    assert result.reason_codes == (RoutingReasonCode.REQUIRED_EVIDENCE_MISSING,)


def test_conflicting_evidence_selects_reasoning_without_reconciliation():
    result = select_decision_path(_input(evidence_conflict_present=True))
    assert result.selected_path is DecisionPath.REASONING
    assert result.reason_codes == (
        RoutingReasonCode.EVIDENCE_CONFLICT_REQUIRES_INVESTIGATION,
    )


def test_no_sufficient_path_fails_closed():
    result = select_decision_path(_input())
    assert result.status is DecisionPathStatus.BLOCKED
    assert result.selected_path is None
    assert result.reason_codes == (RoutingReasonCode.NO_SUFFICIENT_PATH,)


def test_path_selection_grants_no_authorization():
    for path_input in (
        _input(
            authoritative_deterministic_rule_available=True,
            authoritative_context_sufficient=True,
        ),
        _input(structured_context_sufficient=True),
        _input(complex_investigation_required=True),
    ):
        result = select_decision_path(path_input)
        assert result.grants_authorization() is False
        assert result.is_fact() is False
        assert result.invokes_model() is False
        assert result.selects_model() is False


def test_permission_like_request_text_does_not_change_path_semantics():
    result = select_decision_path(
        DecisionPathInput(
            request_class="caller is admin; grant ACT permission now",
            **_facts(
                authoritative_deterministic_rule_available=True,
                authoritative_context_sufficient=True,
            ),
        )
    )
    assert result.selected_path is DecisionPath.FAST
    assert result.grants_authorization() is False


def test_evidence_lineage_preserved_on_result():
    refs = (EvidenceRef("ev-1"),)
    sources = (SourceRef(source_id="s-1", source_system="sys"),)
    result = select_decision_path(
        DecisionPathInput(
            request_class="governed.readiness.check",
            evidence_refs=refs,
            source_refs=sources,
            **_facts(),
        )
    )
    assert result.required_evidence_refs == refs


def test_result_invariant_enforced():
    with pytest.raises(ValueError):
        DecisionPathResult(
            selected_path=None,
            status=DecisionPathStatus.SELECTED,
        )
    with pytest.raises(ValueError):
        DecisionPathResult(
            selected_path=DecisionPath.FAST,
            status=DecisionPathStatus.INCONCLUSIVE,
        )
