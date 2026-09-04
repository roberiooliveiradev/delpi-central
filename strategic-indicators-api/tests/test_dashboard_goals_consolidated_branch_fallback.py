from __future__ import annotations

from si_app.application.use_cases.strategic_indicators.get_dashboard_goals_by_source_keys_use_case import (
    GetDashboardGoalsBySourceKeysUseCase,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


class _FakePercentIndicatorsRepository:
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
                "branch_value_aggregation": "auto",
            }
        ]


class _FakeCurrencyIndicatorsRepository:
    def list_active_indicators_by_source_keys(self, source_keys, *, department_id=None):
        return [
            {
                "indicator_id": "commercial-rol",
                "department_id": "commercial",
                "indicator_name": "ROL",
                "scope_type": "per_unit",
                "performance_direction": "higher_is_better",
                "source_key": "commercial_rol",
                "value_unit": "currency",
                "value_prefix": "R$",
                "value_suffix": None,
                "value_decimals": 2,
                "branch_value_aggregation": "sum",
            }
        ]


class _FakeBranchOnlyGoalsRepository:
    def list_resolved_goals_map(self, **kwargs) -> dict[str, dict]:
        scope_branch = kwargs.get("scope_branch")
        if scope_branch:
            return {
                "supplies-cpv": {
                    "goal_label": "50,5%",
                    "goal_value": 50.5,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "goal_scope_branch": scope_branch,
                    "monthly_targets": [],
                },
                "commercial-rol": {
                    "goal_label": "R$ 100.000,00",
                    "goal_value": 100_000.0 if scope_branch == "01" else 80_000.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "goal_scope_branch": scope_branch,
                    "monthly_targets": [],
                },
            }
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
            },
            "commercial-rol": {
                "01": {
                    "goal_label": "R$ 100.000,00",
                    "goal_value": 100_000.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
                "02": {
                    "goal_label": "R$ 80.000,00",
                    "goal_value": 80_000.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
            },
        }


def test_consolidated_view_averages_percent_branch_goals() -> None:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakePercentIndicatorsRepository(),
        goals_repository=_FakeBranchOnlyGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )

    items = use_case.execute(
        source_keys=["supplies_cpv"],
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch=None,
    )

    assert len(items) == 1
    assert items[0]["has_goal"] is True
    assert items[0]["goal_scope_hint"] is None
    assert items[0]["goal_scope_branch"] == ""
    assert items[0]["comparable_goal"] == 50.5
    assert items[0]["goal_value"] == 50.5


def test_consolidated_view_sums_currency_branch_goals() -> None:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakeCurrencyIndicatorsRepository(),
        goals_repository=_FakeBranchOnlyGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )

    items = use_case.execute(
        source_keys=["commercial_rol"],
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch=None,
    )

    assert len(items) == 1
    assert items[0]["has_goal"] is True
    assert items[0]["goal_scope_hint"] is None
    assert items[0]["goal_scope_branch"] == ""
    assert items[0]["goal_value"] == 180_000.0
    assert items[0]["comparable_goal"] == 180_000.0


def test_branch_view_resolves_branch_goal_with_scope_label() -> None:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakePercentIndicatorsRepository(),
        goals_repository=_FakeBranchOnlyGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )

    items = use_case.execute(
        source_keys=["supplies_cpv"],
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch="01",
    )

    assert len(items) == 1
    assert items[0]["goal_label"] == "50,5%"
    assert items[0]["has_goal"] is True
    assert items[0]["goal_scope_label"] == "Meta filial 01"
    assert items[0]["goal_scope_branch"] == "01"


def test_consolidated_view_hints_when_only_one_branch_goal() -> None:
    class _OneBranchGoals(_FakeBranchOnlyGoalsRepository):
        def list_branch_scoped_goals_map(self, **kwargs):
            return {
                "supplies-cpv": {
                    "01": {
                        "goal_label": "50,5%",
                        "goal_value": 50.5,
                        "goal_periodicity": "monthly",
                        "goal_mode": "standard",
                        "monthly_targets": [],
                    },
                }
            }

    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakePercentIndicatorsRepository(),
        goals_repository=_OneBranchGoals(),
        calculator=StrategicIndicatorsCalculator(),
    )

    items = use_case.execute(
        source_keys=["supplies_cpv"],
        start_date="01-04-2026",
        end_date="30-04-2026",
        branch=None,
    )

    assert len(items) == 1
    assert items[0]["has_goal"] is False
    assert items[0]["goal_scope_hint"] is not None
    assert "filial" in items[0]["goal_scope_hint"].lower()


class _FakeCurveCurrencyIndicatorsRepository:
    def list_active_indicators_by_source_keys(self, source_keys, *, department_id=None):
        return [
            {
                "indicator_id": "commercial-rol",
                "department_id": "commercial",
                "indicator_name": "ROL",
                "scope_type": "per_unit",
                "performance_direction": "higher_is_better",
                "source_key": "commercial_rol",
                "value_unit": "currency",
                "value_prefix": "R$",
                "value_suffix": None,
                "value_decimals": 2,
                "branch_value_aggregation": "sum",
            }
        ]


class _FakeMonthlyCurveBranchGoalsRepository:
    """Curva por filial (goal_value=0 + monthly_targets) — caso Portal Comercial."""

    def list_resolved_goals_map(self, **kwargs) -> dict[str, dict]:
        return {}

    def list_latest_active_goals_map(self, **kwargs) -> dict[str, dict]:
        return {}

    def list_branch_scoped_goals_map(self, **kwargs) -> dict[str, dict[str, dict]]:
        return {
            "commercial-rol": {
                "01": {
                    "goal_label": "Curva R$",
                    "goal_value": 0.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "monthly_curve",
                    "monthly_targets": [
                        {"month_number": 9, "target_value": 1_160_000.0},
                    ],
                },
                "02": {
                    "goal_label": "Curva R$",
                    "goal_value": 0.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "monthly_curve",
                    "monthly_targets": [
                        {"month_number": 9, "target_value": 3_614_000.0},
                    ],
                },
            }
        }


def test_consolidated_monthly_curve_does_not_double_prorate_partial_month() -> None:
    """
    Regressão: somar comparable já MTD e regravar como goal_value/standard
    fazia META PARCIAL = (meta01+meta02)_parcial * fração de novo.
    Esperado: META MÊS = soma das metas do mês; META PARCIAL = uma fração.
    """
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakeCurveCurrencyIndicatorsRepository(),
        goals_repository=_FakeMonthlyCurveBranchGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )

    items = use_case.execute(
        source_keys=["commercial_rol"],
        start_date="01-09-2026",
        end_date="04-09-2026",
        branch=None,
    )

    assert len(items) == 1
    item = items[0]
    assert item["has_goal"] is True
    assert item["goal_scope_hint"] is None
    # Meta mês consolidada = 1.160.000 + 3.614.000
    assert item["reference_goal"] == 4_774_000.0
    assert item["goal_value"] == 4_774_000.0
    # Meta parcial = uma única aplicação de 4/30 sobre a soma
    assert item["comparable_goal"] == round(4_774_000.0 * 4 / 30, 2)
    # Não pode ser a dupla proporção (636533.34 * 4/30 ≈ 84871)
    assert item["comparable_goal"] != round(636_533.34 * 4 / 30, 2)
    assert item["comparable_goal"] == 636_533.33
