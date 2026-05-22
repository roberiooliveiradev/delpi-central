from __future__ import annotations

from si_app.application.use_cases.strategic_indicators.get_dashboard_goals_by_source_keys_use_case import (
    GetDashboardGoalsBySourceKeysUseCase,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


class _FakeIndicatorsRepository:
    def list_active_indicators_by_source_keys(self, source_keys, *, department_id=None):
        return [
            {
                "indicator_id": "supplies-cpv",
                "department_id": "supplies",
                "indicator_name": "CPV",
                "scope_type": "consolidated",
                "performance_direction": "lower_is_better",
                "source_key": "supplies_cpv",
                "value_unit": "percent",
                "value_prefix": None,
                "value_suffix": "%",
                "value_decimals": 2,
            }
        ]


class _FakeGoalsRepository:
    def list_resolved_goals_map(self, **kwargs) -> dict[str, dict]:
        return {}

    def list_latest_active_goals_map(self, **kwargs) -> dict[str, dict]:
        return {}

    def list_branch_scoped_goals_map(self, **kwargs) -> dict[str, dict[str, dict]]:
        return {
            "supplies-cpv": {
                "01": {
                    "goal_label": "50,5%",
                    "goal_value": 50.5,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
                "02": {
                    "goal_label": "50,5%",
                    "goal_value": 50.5,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
            }
        }


def test_consolidated_view_uses_branch_goals_when_consolidated_meta_missing() -> None:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakeIndicatorsRepository(),
        goals_repository=_FakeGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )

    items = use_case.execute(
        source_keys=["supplies_cpv"],
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch=None,
    )

    assert len(items) == 1
    assert items[0]["goal_label"] == "50,5%"
    assert items[0]["has_goal"] is True
