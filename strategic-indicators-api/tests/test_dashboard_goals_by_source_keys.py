from __future__ import annotations

from si_app.application.use_cases.strategic_indicators.get_dashboard_goals_by_source_keys_use_case import (
    GetDashboardGoalsBySourceKeysUseCase,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


class _FakeIndicatorsRepository:
    def list_active_indicators_by_source_keys(
        self,
        source_keys: list[str],
        *,
        department_id: str | None = None,
    ) -> list[dict]:
        return [
            {
                "indicator_id": "commercial-closing-rate",
                "department_id": "commercial",
                "indicator_name": "Taxa de Fechamento",
                "scope_type": "consolidated",
                "performance_direction": "higher_is_better",
                "source_key": "commercial_sales_conversion_rate",
                "value_unit": "percent",
                "value_prefix": None,
                "value_suffix": "%",
                "value_decimals": 2,
            }
        ]


class _FakeGoalsRepository:
    def list_resolved_goals_map(self, **kwargs) -> dict[str, dict]:
        return {
            "commercial-closing-rate": {
                "goal_label": "10%",
                "goal_value": 10.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            }
        }

    def list_latest_active_goals_map(self, **kwargs) -> dict[str, dict]:
        return {}


def test_dashboard_goals_returns_comparable_goal_for_source_key() -> None:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakeIndicatorsRepository(),
        goals_repository=_FakeGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )

    items = use_case.execute(
        source_keys=["commercial_sales_conversion_rate"],
        start_date="01-04-2026",
        end_date="30-04-2026",
    )

    assert len(items) == 1
    assert items[0]["source_key"] == "commercial_sales_conversion_rate"
    assert items[0]["goal_label"] == "10%"
    assert items[0]["comparable_goal"] == 10.0
    assert items[0]["has_goal"] is True
