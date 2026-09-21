from __future__ import annotations

from tm_app.application.services.dashboard_strategic_indicators_service import (
    DashboardStrategicIndicatorsService,
    flatten_si_goal_fields,
    normalize_si_branch,
)
from tm_app.domain.strategic_indicators_context import (
    GROSS_SAVINGS_INDICATOR_ID,
    GROSS_SAVINGS_SOURCE_KEY,
    STRATEGIC_INDICATORS_DEPARTMENT_ID,
)


class _FakePort:
    def __init__(
        self,
        *,
        score=None,
        indicators=None,
        goals=None,
    ) -> None:
        self.score = score
        self.indicators = indicators
        self.goals = goals
        self.calls: list[tuple[str, dict]] = []

    def get_department_score(self, **kwargs):
        self.calls.append(("score", kwargs))
        return self.score

    def get_department_indicators(self, **kwargs):
        self.calls.append(("indicators", kwargs))
        return self.indicators

    def list_dashboard_goals(self, **kwargs):
        self.calls.append(("goals", kwargs))
        return self.goals


SI_GOAL_FIXTURE = {
    "source_key": GROSS_SAVINGS_SOURCE_KEY,
    "indicator_id": GROSS_SAVINGS_INDICATOR_ID,
    "goal_label": "Meta Transforma+",
    "goal_value": 12000,
    "comparable_goal": 8000,
    "reference_goal": 12000,
    "has_goal": True,
    "goal_period_kind": "partial",
    "goal_scope_label": "Meta consolidada",
    "performance_direction": "higher_is_better",
    "value_prefix": "R$",
    "value_decimals": 2,
}


def test_engineering_ids_are_canonical():
    assert STRATEGIC_INDICATORS_DEPARTMENT_ID == "engineering"
    assert GROSS_SAVINGS_INDICATOR_ID == "engineering-transforma-plus"
    assert GROSS_SAVINGS_SOURCE_KEY == "transforma_mais"


def test_normalize_si_branch_omits_consolidated_tokens():
    assert normalize_si_branch("all") is None
    assert normalize_si_branch("01") == "01"
    assert normalize_si_branch("") is None


def test_flatten_copies_si_fields_without_formula():
    fields = flatten_si_goal_fields(SI_GOAL_FIXTURE)
    assert fields["comparable_goal"] == 8000
    assert fields["reference_goal"] == 12000
    assert fields["goal_period_kind"] == "partial"
    assert fields["goal_scope_label"] == "Meta consolidada"
    assert fields["performance_direction"] == "higher_is_better"
    assert fields["has_goal"] is True


def test_get_program_context_maps_gross_savings_and_global_idd():
    port = _FakePort(
        score={
            "department_id": "engineering",
            "score": 9.4,
            "classification": "Excelência Integrada",
            "partial_success": False,
        },
        indicators={
            "department_id": "engineering",
            "score": 9.4,
            "indicators": [
                {"indicator_id": GROSS_SAVINGS_INDICATOR_ID, "score": 8.5},
                {"indicator_id": "engineering-projects-on-time", "score": 7.1},
            ],
        },
        goals={"items": [SI_GOAL_FIXTURE]},
    )
    result = DashboardStrategicIndicatorsService(port).get_program_context(
        competence="2026-09",
        start_date="2026-09-01",
        end_date="2026-09-21",
        branch="all",
    )

    assert result["available"] is True
    assert result["strategic_indicators_department"] == "engineering"
    assert result["branch"] is None
    assert result["department_idd"]["score"] == 9.4
    assert result["department_idd"]["classification"] == "Excelência Integrada"
    assert result["gross_savings"]["indicator_id"] == GROSS_SAVINGS_INDICATOR_ID
    assert result["gross_savings"]["comparable_goal"] == 8000
    assert result["gross_savings"]["reference_goal"] == 12000
    assert result["gross_savings"]["score"] == 8.5
    assert result["gross_savings"]["performance_direction"] == "higher_is_better"
    for kind, kwargs in port.calls:
        assert kwargs["department_id"] == "engineering"
        if kind != "goals":
            assert kwargs["branch"] is None


def test_value_vs_target_uses_si_returned_fields_not_local_formula():
    above = {**SI_GOAL_FIXTURE, "comparable_goal": 100}
    equal = {**SI_GOAL_FIXTURE, "comparable_goal": 200}
    below = {**SI_GOAL_FIXTURE, "comparable_goal": 300}
    for fixture, expected in ((above, 100.0), (equal, 200.0), (below, 300.0)):
        fields = flatten_si_goal_fields(fixture)
        assert fields["comparable_goal"] == expected


def test_fail_closed_when_si_returns_nothing():
    result = DashboardStrategicIndicatorsService(_FakePort()).get_program_context()
    assert result["available"] is False
    assert result["department_idd"] is None
    assert result["gross_savings"] is None
    assert result["indicators"] == []


def test_score_present_without_goal_still_exposes_idd():
    port = _FakePort(
        indicators={
            "indicators": [{"indicator_id": GROSS_SAVINGS_INDICATOR_ID, "score": 6.2}],
        }
    )
    result = DashboardStrategicIndicatorsService(port).get_program_context()
    assert result["available"] is True
    assert result["gross_savings"]["score"] == 6.2
    assert result["gross_savings"]["has_goal"] is False
    assert result["gross_savings"]["comparable_goal"] is None
