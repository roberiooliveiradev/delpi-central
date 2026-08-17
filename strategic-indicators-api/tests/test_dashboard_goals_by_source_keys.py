from __future__ import annotations

from si_app.application.use_cases.strategic_indicators.get_dashboard_goals_by_source_keys_use_case import (
    GetDashboardGoalsBySourceKeysUseCase,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from tests.fixtures.si_goal_contract_cases import (
    CASE_A_EXACT,
    CASE_B_PARTIAL,
    CASE_CURVE,
    assert_triad_invariants,
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
                "goal_scope_branch": "",
                "monthly_targets": [],
            }
        }

    def list_branch_scoped_goals_map(self, **kwargs) -> dict[str, dict[str, dict]]:
        return {}

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
    assert items[0]["goal_value"] == 10.0
    assert items[0]["reference_goal"] == 10.0
    assert items[0]["has_goal"] is True
    assert items[0]["goal_scope_branch"] == ""
    assert items[0]["goal_scope_label"] == "Meta consolidada"
    assert items[0]["goal_aggregation"] == "average"
    assert items[0]["goal_period_partial"] is False
    assert items[0]["goal_period_kind"] == "exact"


def test_dashboard_goals_partial_month_prorata_and_flags() -> None:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakeIndicatorsRepository(),
        goals_repository=_FakeGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )

    items = use_case.execute(
        source_keys=["commercial_sales_conversion_rate"],
        start_date="01-04-2026",
        end_date="15-04-2026",
    )

    assert len(items) == 1
    # percent + mês incompleto → soma parcelas diárias (10 × 15/30)
    assert items[0]["comparable_goal"] == 5.0
    assert items[0]["goal_value"] == 10.0
    assert items[0]["reference_goal"] == 10.0
    assert items[0]["goal_aggregation"] == "sum"
    assert items[0]["goal_period_partial"] is True
    assert items[0]["goal_period_kind"] == "partial"

class _FakeCurveGoalsRepository:
    def list_resolved_goals_map(self, **kwargs) -> dict[str, dict]:
        return {
            "commercial-closing-rate": {
                "goal_label": "curva",
                "goal_value": 0.0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "goal_scope_branch": "",
                "monthly_targets": [
                    {"month_number": 1, "target_value": 90.0},
                    {"month_number": 2, "target_value": 100.0},
                    {"month_number": 3, "target_value": 110.0},
                ],
            }
        }

    def list_branch_scoped_goals_map(self, **kwargs) -> dict[str, dict[str, dict]]:
        return {}

    def list_latest_active_goals_map(self, **kwargs) -> dict[str, dict]:
        return {}


def test_dashboard_goals_curve_reference_goal_is_average_of_filter_months() -> None:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakeIndicatorsRepository(),
        goals_repository=_FakeCurveGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )

    items = use_case.execute(
        source_keys=["commercial_sales_conversion_rate"],
        start_date="01-01-2026",
        end_date="28-02-2026",
    )

    assert len(items) == 1
    assert items[0]["goal_value"] == 0.0
    assert items[0]["goal_mode"] == "monthly_curve"
    assert items[0]["reference_goal"] == 95.0
    # comparable_goal é o nível do período (prorata/média ponderada), distinto da média simples
    assert items[0]["comparable_goal"] is not None
    assert items[0]["comparable_goal"] > 0


def test_dashboard_goals_partial_matches_contract_case_b() -> None:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakeIndicatorsRepository(),
        goals_repository=_FakeGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )
    # Fake repo uses percent + goal 10; adapt CASE_B dates with percent prorata 10*17/31
    items = use_case.execute(
        source_keys=["commercial_sales_conversion_rate"],
        start_date=CASE_B_PARTIAL["start_date"],
        end_date=CASE_B_PARTIAL["end_date"],
    )
    assert len(items) == 1
    assert items[0]["goal_value"] == 10.0
    assert items[0]["reference_goal"] == 10.0
    assert items[0]["goal_period_kind"] == "partial"
    assert abs(float(items[0]["comparable_goal"]) - round(10.0 * 17 / 31, 2)) < 0.02
    assert items[0]["goal_value"] != items[0]["comparable_goal"]


def test_dashboard_goals_exact_matches_contract_case_a() -> None:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakeIndicatorsRepository(),
        goals_repository=_FakeGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )
    items = use_case.execute(
        source_keys=["commercial_sales_conversion_rate"],
        start_date=CASE_A_EXACT["start_date"],
        end_date=CASE_A_EXACT["end_date"],
    )
    assert_triad_invariants(CASE_A_EXACT, items[0])


def test_dashboard_goals_curve_matches_contract_reference() -> None:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakeIndicatorsRepository(),
        goals_repository=_FakeCurveGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )
    items = use_case.execute(
        source_keys=["commercial_sales_conversion_rate"],
        start_date=CASE_CURVE["start_date"],
        end_date=CASE_CURVE["end_date"],
    )
    assert items[0]["goal_value"] == CASE_CURVE["expected_goal_value"]
    assert items[0]["reference_goal"] == CASE_CURVE["expected_reference_goal"]
    assert items[0]["comparable_goal"] != items[0]["goal_value"]