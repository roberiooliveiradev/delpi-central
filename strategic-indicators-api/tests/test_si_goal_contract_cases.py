"""Smoke: SI goal contract fixture loads and invariants hold on expected payloads."""

from __future__ import annotations

import pytest

from tests.fixtures.si_goal_contract_cases import (
    CASE_B_PARTIAL,
    PARTIAL_SI_META_PAYLOAD,
    SI_GOAL_CONTRACT_CASES,
    SI_GOAL_FIELD_KEYS,
    SI_GOAL_FIELD_LABELS_PT,
    assert_triad_invariants,
    case_by_id,
    cases_by_letter,
)


def test_si_goal_contract_cases_cover_matrix_a_to_h() -> None:
    letters = {c["matrix_letter"] for c in SI_GOAL_CONTRACT_CASES}
    assert {"A", "B", "C", "D", "E", "F", "G", "H"}.issubset(letters)
    assert len(SI_GOAL_CONTRACT_CASES) >= 8


def test_si_goal_field_labels_pt_cover_triad() -> None:
    for key in SI_GOAL_FIELD_KEYS:
        assert key in SI_GOAL_FIELD_LABELS_PT
        assert SI_GOAL_FIELD_LABELS_PT[key]


@pytest.mark.parametrize("case", SI_GOAL_CONTRACT_CASES, ids=lambda c: c["case_id"])
def test_si_goal_contract_case_self_consistent(case: dict) -> None:
    payload = {
        "goal_value": case["expected_goal_value"],
        "comparable_goal": case["expected_comparable_goal"],
        "reference_goal": case["expected_reference_goal"],
        "value": case["expected_comparable_goal"],
    }
    assert_triad_invariants(case, payload)
    if case["goal_value_equals_comparable"]:
        assert case["expected_goal_value"] == case["expected_comparable_goal"]
    else:
        assert case["expected_goal_value"] != case["expected_comparable_goal"]


def test_partial_si_meta_payload_matches_case_b() -> None:
    assert_triad_invariants(CASE_B_PARTIAL, PARTIAL_SI_META_PAYLOAD)
    assert PARTIAL_SI_META_PAYLOAD["goal_value"] == 8.0
    assert PARTIAL_SI_META_PAYLOAD["value"] == PARTIAL_SI_META_PAYLOAD["comparable_goal"]
    assert abs(float(PARTIAL_SI_META_PAYLOAD["comparable_goal"]) - 4.39) < 0.01


def test_case_by_id_and_letter_helpers() -> None:
    assert case_by_id("partial_month_prorata")["matrix_letter"] == "B"
    assert len(cases_by_letter("A")) >= 1
    with pytest.raises(KeyError):
        case_by_id("does-not-exist")
