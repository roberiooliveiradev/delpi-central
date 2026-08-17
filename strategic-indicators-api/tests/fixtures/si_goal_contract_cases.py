"""Canonical SI goal triad contract cases (matrix A–H).

Contract:
- goal_value: registered goal (never overwritten by prorata)
- comparable_goal: period goal (prorata / sum / average)
- reference_goal: "Meta mês" reference (standard = goal_value; curve = avg of months)
- value on *_meta routes: alias of comparable_goal (not registered)

Bounded to this package — do not import from other apps.
"""

from __future__ import annotations

from typing import Any, TypedDict


class SiGoalContractCase(TypedDict):
    case_id: str
    matrix_letter: str
    description: str
    start_date: str
    end_date: str
    competence: str
    goal_mode: str
    value_unit: str
    registered_goal_value: float
    monthly_targets: list[dict[str, Any]]
    expected_goal_value: float
    expected_comparable_goal: float
    expected_reference_goal: float
    expected_period_kind: str
    expected_period_partial: bool
    goal_value_equals_comparable: bool
    notes: str


# --- Matrix A–H (product scenarios) ---

CASE_A_EXACT: SiGoalContractCase = {
    "case_id": "exact_full_month",
    "matrix_letter": "A",
    "description": "Full civil month: triad fields equal; UI shows single Meta line",
    "start_date": "01-04-2026",
    "end_date": "30-04-2026",
    "competence": "2026-04",
    "goal_mode": "standard",
    "value_unit": "percent",
    "registered_goal_value": 10.0,
    "monthly_targets": [],
    "expected_goal_value": 10.0,
    "expected_comparable_goal": 10.0,
    "expected_reference_goal": 10.0,
    "expected_period_kind": "exact",
    "expected_period_partial": False,
    "goal_value_equals_comparable": True,
    "notes": "UI: one line labeled Meta",
}

CASE_B_PARTIAL: SiGoalContractCase = {
    "case_id": "partial_month_prorata",
    "matrix_letter": "B",
    "description": "Partial month: registered ≠ comparable; reference = registered (standard)",
    "start_date": "01-08-2026",
    "end_date": "17-08-2026",
    "competence": "2026-08",
    "goal_mode": "standard",
    "value_unit": "count",
    # Kaizen-like: 8 ideas/month → prorata 8 * 17/31 ≈ 4.39
    "registered_goal_value": 8.0,
    "monthly_targets": [],
    "expected_goal_value": 8.0,
    "expected_comparable_goal": round(8.0 * 17 / 31, 2),
    "expected_reference_goal": 8.0,
    "expected_period_kind": "partial",
    "expected_period_partial": True,
    "goal_value_equals_comparable": False,
    "notes": "TV Meta cadastrada must stay 8.0; value/comparable ≈ 4.39",
}

CASE_B_PARTIAL_PPM: SiGoalContractCase = {
    "case_id": "partial_month_ppm",
    "matrix_letter": "B",
    "description": "Partial PPM: registered 1400; comparable ≈ 767.74",
    "start_date": "01-08-2026",
    "end_date": "17-08-2026",
    "competence": "2026-08",
    "goal_mode": "standard",
    "value_unit": "ppm",
    "registered_goal_value": 1400.0,
    "monthly_targets": [],
    "expected_goal_value": 1400.0,
    "expected_comparable_goal": round(1400.0 * 17 / 31, 2),
    "expected_reference_goal": 1400.0,
    "expected_period_kind": "partial",
    "expected_period_partial": True,
    "goal_value_equals_comparable": False,
    "notes": "branch_view keeps goal_value=1400; unit_goals holds comparable",
}

CASE_C_ACCUMULATED: SiGoalContractCase = {
    "case_id": "accumulated_ytd_percent",
    "matrix_letter": "C",
    "description": "YTD multi-month: kind accumulated; goal_value intact",
    "start_date": "01-01-2026",
    "end_date": "30-04-2026",
    "competence": "2026-04",
    "goal_mode": "standard",
    "value_unit": "percent",
    "registered_goal_value": 10.0,
    "monthly_targets": [],
    "expected_goal_value": 10.0,
    # percent multi-month → average of monthly goals (exact months) = 10.0
    "expected_comparable_goal": 10.0,
    "expected_reference_goal": 10.0,
    "expected_period_kind": "accumulated",
    "expected_period_partial": False,
    "goal_value_equals_comparable": True,
    "notes": "Prefix acumulada in UI; registered goal unchanged",
}

CASE_D_CONSOLIDATED_HINT: SiGoalContractCase = {
    "case_id": "consolidated_goal_scope_hint",
    "matrix_letter": "D",
    "description": "Consolidated without unit: UI omits numeric goals when goal_scope_hint set",
    "start_date": "01-04-2026",
    "end_date": "30-04-2026",
    "competence": "2026-04",
    "goal_mode": "standard",
    "value_unit": "currency",
    "registered_goal_value": 1_000_000.0,
    "monthly_targets": [],
    "expected_goal_value": 1_000_000.0,
    "expected_comparable_goal": 1_000_000.0,
    "expected_reference_goal": 1_000_000.0,
    "expected_period_kind": "exact",
    "expected_period_partial": False,
    "goal_value_equals_comparable": True,
    "notes": "Consumers: goal_scope_hint → no Meta mês numbers (plugin-ui)",
}

CASE_E_CHAT_TRIAD: SiGoalContractCase = {
    "case_id": "chat_triad_highlights",
    "matrix_letter": "E",
    "description": "Chat: triad in highlights; absent from skipFieldKeys",
    "start_date": "01-08-2026",
    "end_date": "17-08-2026",
    "competence": "2026-08",
    "goal_mode": "standard",
    "value_unit": "count",
    "registered_goal_value": 8.0,
    "monthly_targets": [],
    "expected_goal_value": 8.0,
    "expected_comparable_goal": round(8.0 * 17 / 31, 2),
    "expected_reference_goal": 8.0,
    "expected_period_kind": "partial",
    "expected_period_partial": True,
    "goal_value_equals_comparable": False,
    "notes": "Asserted in minha-delpi-ai-api content gates",
}

CASE_F_TV_DEDUPE_EQUAL: SiGoalContractCase = {
    "case_id": "tv_dedupe_equal_values",
    "matrix_letter": "F",
    "description": "TV meta: equal triad values → single kpiMetric value",
    "start_date": "01-04-2026",
    "end_date": "30-04-2026",
    "competence": "2026-04",
    "goal_mode": "standard",
    "value_unit": "percent",
    "registered_goal_value": 10.0,
    "monthly_targets": [],
    "expected_goal_value": 10.0,
    "expected_comparable_goal": 10.0,
    "expected_reference_goal": 10.0,
    "expected_period_kind": "exact",
    "expected_period_partial": False,
    "goal_value_equals_comparable": True,
    "notes": "TV enrichment dedupe when values equal",
}

CASE_G_TV_DISTINCT: SiGoalContractCase = {
    "case_id": "tv_distinct_goal_value_vs_value",
    "matrix_letter": "G",
    "description": "TV: value (comparable) ≠ goal_value → distinct metrics",
    "start_date": "01-08-2026",
    "end_date": "17-08-2026",
    "competence": "2026-08",
    "goal_mode": "standard",
    "value_unit": "count",
    "registered_goal_value": 8.0,
    "monthly_targets": [],
    "expected_goal_value": 8.0,
    "expected_comparable_goal": round(8.0 * 17 / 31, 2),
    "expected_reference_goal": 8.0,
    "expected_period_kind": "partial",
    "expected_period_partial": True,
    "goal_value_equals_comparable": False,
    "notes": "Meta cadastrada binds goal_value, not value",
}

CASE_H_HUBS_ENRICH: SiGoalContractCase = {
    "case_id": "hubs_enrich_filial_all",
    "matrix_letter": "H",
    "description": "Hubs enrich with filial=all: flatten keeps registered ≠ comparable",
    "start_date": "01-08-2026",
    "end_date": "17-08-2026",
    "competence": "2026-08",
    "goal_mode": "standard",
    "value_unit": "count",
    "registered_goal_value": 8.0,
    "monthly_targets": [],
    "expected_goal_value": 8.0,
    "expected_comparable_goal": round(8.0 * 17 / 31, 2),
    "expected_reference_goal": 8.0,
    "expected_period_kind": "partial",
    "expected_period_partial": True,
    "goal_value_equals_comparable": False,
    "notes": "api-delpi Kaizen ideas_goal / LMP / PPM enrich",
}

CASE_CURVE: SiGoalContractCase = {
    "case_id": "monthly_curve_reference_average",
    "matrix_letter": "B",
    "description": "Curve: goal_value=0; reference_goal = avg of overlapping months",
    "start_date": "01-01-2026",
    "end_date": "28-02-2026",
    "competence": "2026-02",
    "goal_mode": "monthly_curve",
    "value_unit": "percent",
    "registered_goal_value": 0.0,
    "monthly_targets": [
        {"month_number": 1, "target_value": 90.0},
        {"month_number": 2, "target_value": 100.0},
        {"month_number": 3, "target_value": 110.0},
    ],
    "expected_goal_value": 0.0,
    "expected_comparable_goal": 95.0,
    "expected_reference_goal": 95.0,
    "expected_period_kind": "exact",
    "expected_period_partial": False,
    "goal_value_equals_comparable": False,
    "notes": "reference_goal averages Jan+Feb targets",
}

CASE_BRANCH_VIEW: SiGoalContractCase = {
    "case_id": "branch_view_registered_vs_unit_goals",
    "matrix_letter": "B",
    "description": "Branch view: goal_value = registered; comparable only in unit_goals",
    "start_date": "01-08-2026",
    "end_date": "17-08-2026",
    "competence": "2026-08",
    "goal_mode": "standard",
    "value_unit": "ppm",
    "registered_goal_value": 1400.0,
    "monthly_targets": [],
    "expected_goal_value": 1400.0,
    "expected_comparable_goal": round(1400.0 * 17 / 31, 2),
    "expected_reference_goal": 1400.0,
    "expected_period_kind": "partial",
    "expected_period_partial": True,
    "goal_value_equals_comparable": False,
    "notes": "Calculator branch path must not assign comparable to goal_value",
}

SI_GOAL_CONTRACT_CASES: list[SiGoalContractCase] = [
    CASE_A_EXACT,
    CASE_B_PARTIAL,
    CASE_B_PARTIAL_PPM,
    CASE_C_ACCUMULATED,
    CASE_D_CONSOLIDATED_HINT,
    CASE_E_CHAT_TRIAD,
    CASE_F_TV_DEDUPE_EQUAL,
    CASE_G_TV_DISTINCT,
    CASE_H_HUBS_ENRICH,
    CASE_CURVE,
    CASE_BRANCH_VIEW,
]

SI_GOAL_FIELD_KEYS: tuple[str, ...] = (
    "goal_value",
    "comparable_goal",
    "reference_goal",
)

SI_GOAL_FIELD_LABELS_PT: dict[str, str] = {
    "goal_value": "Meta cadastrada",
    "comparable_goal": "Meta do período",
    "reference_goal": "Meta mês (referência)",
}

# Partial payload shape for gateway mocks (api-delpi / TV consumers mirror locally).
PARTIAL_SI_META_PAYLOAD: dict[str, Any] = {
    "goal_value": CASE_B_PARTIAL["expected_goal_value"],
    "comparable_goal": CASE_B_PARTIAL["expected_comparable_goal"],
    "reference_goal": CASE_B_PARTIAL["expected_reference_goal"],
    "value": CASE_B_PARTIAL["expected_comparable_goal"],
    "goal_mode": "standard",
    "goal_period_kind": "partial",
    "goal_period_partial": True,
}


def assert_triad_invariants(case: SiGoalContractCase, actual: dict[str, Any]) -> None:
    """Raise AssertionError if actual payload violates the case contract."""
    assert actual.get("goal_value") == case["expected_goal_value"], (
        f"{case['case_id']}: goal_value must stay registered "
        f"({case['expected_goal_value']}), got {actual.get('goal_value')}"
    )
    comparable = actual.get("comparable_goal")
    assert comparable is not None
    assert abs(float(comparable) - case["expected_comparable_goal"]) < 0.02, (
        f"{case['case_id']}: comparable_goal expected "
        f"{case['expected_comparable_goal']}, got {comparable}"
    )
    assert actual.get("reference_goal") == case["expected_reference_goal"], (
        f"{case['case_id']}: reference_goal expected "
        f"{case['expected_reference_goal']}, got {actual.get('reference_goal')}"
    )
    if not case["goal_value_equals_comparable"]:
        assert float(actual["goal_value"]) != float(comparable), (
            f"{case['case_id']}: goal_value must differ from comparable_goal "
            f"when period is partial/curve"
        )
    value = actual.get("value")
    if value is not None and case["matrix_letter"] in {"B", "G", "E", "H"}:
        assert abs(float(value) - float(comparable)) < 0.02, (
            f"{case['case_id']}: value on meta route must alias comparable_goal"
        )


def cases_by_letter(letter: str) -> list[SiGoalContractCase]:
    return [c for c in SI_GOAL_CONTRACT_CASES if c["matrix_letter"] == letter]


def case_by_id(case_id: str) -> SiGoalContractCase:
    for case in SI_GOAL_CONTRACT_CASES:
        if case["case_id"] == case_id:
            return case
    raise KeyError(f"Unknown SI goal contract case_id={case_id!r}")
