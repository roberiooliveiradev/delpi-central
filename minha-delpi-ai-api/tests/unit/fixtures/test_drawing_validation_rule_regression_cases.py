"""Contrato dos casos de regressão por regra — Fase C."""

from tests.fixtures.drawing_validation_rule_regression_cases import (
    DRAWING_VALIDATION_RULE_CASES,
    cases_for_rule,
    rule_ids_with_cases,
)


def test_rule_cases_have_rule_id_and_category():
    for case in DRAWING_VALIDATION_RULE_CASES:
        assert case.rule_id
        assert case.category
        assert case.id.startswith("R-")


def test_rule_case_ids_unique():
    ids = [case.id for case in DRAWING_VALIDATION_RULE_CASES]

    assert len(ids) == len(set(ids))


def test_revision_cross_check_has_cases():
    assert cases_for_rule("revision_cross_check")


def test_bom_comparison_has_multiple_cases():
    assert len(cases_for_rule("bom_comparison")) >= 2


def test_rule_ids_non_empty():
    assert rule_ids_with_cases()
