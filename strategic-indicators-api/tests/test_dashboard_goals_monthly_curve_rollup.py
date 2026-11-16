from __future__ import annotations

import pytest

from si_app.application.use_cases.strategic_indicators.get_dashboard_goals_by_source_keys_use_case import (
    GetDashboardGoalsBySourceKeysUseCase,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


def _branch_01_curve() -> list[dict]:
    # Filial 01: 12 x 950.000,00 = 11.400.000,00
    return [
        {"month_number": month, "target_value": 950_000.0}
        for month in range(1, 13)
    ]


def _branch_02_curve() -> list[dict]:
    # Filial 02: curva nao uniforme somando exatamente 40.600.000,00.
    values = [
        2_566_000.0,
        3_454_000.0,
        3_446_000.0,
        3_459_333.33,
        3_459_333.33,
        3_459_333.33,
        3_459_333.33,
        3_459_333.33,
        3_459_333.33,
        3_459_333.33,
        3_459_333.33,
        3_459_333.36,
    ]
    return [
        {"month_number": month, "target_value": value}
        for month, value in enumerate(values, start=1)
    ]


def _merged_monthly_targets() -> list[dict]:
    merged = []
    b01 = {item["month_number"]: item["target_value"] for item in _branch_01_curve()}
    b02 = {item["month_number"]: item["target_value"] for item in _branch_02_curve()}
    for month in range(1, 13):
        merged.append(
            {"month_number": month, "target_value": round(b01[month] + b02[month], 2)}
        )
    return merged


class _FakeRolIndicatorsRepository:
    def list_active_indicators_by_source_keys(
        self,
        source_keys: list[str],
        *,
        department_id: str | None = None,
    ) -> list[dict]:
        return [
            {
                "indicator_id": "commercial-rol",
                "department_id": "commercial",
                "indicator_name": "ROL",
                "scope_type": "consolidated",
                "performance_direction": "higher_is_better",
                "source_key": "commercial_rol",
                "value_unit": "currency",
                "value_prefix": "R$",
                "value_suffix": None,
                "value_decimals": 2,
            }
        ]


class _FakeRolBranchCurveGoalsRepository:
    """Sem meta consolidada (''): apenas metas por filial em curva mensal."""

    def list_resolved_goals_map(self, **kwargs) -> dict[str, dict]:
        return {}

    def list_branch_scoped_goals_map(self, **kwargs) -> dict[str, dict[str, dict]]:
        return {
            "commercial-rol": {
                "01": {
                    "goal_label": "Meta filial 01",
                    "goal_value": 0.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "monthly_curve",
                    "goal_scope_branch": "01",
                    "monthly_targets": _branch_01_curve(),
                },
                "02": {
                    "goal_label": "Meta filial 02",
                    "goal_value": 0.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "monthly_curve",
                    "goal_scope_branch": "02",
                    "monthly_targets": _branch_02_curve(),
                },
            }
        }

    def list_latest_active_goals_map(self, **kwargs) -> dict[str, dict]:
        return {}


def _execute(*, start_date: str, end_date: str) -> dict:
    use_case = GetDashboardGoalsBySourceKeysUseCase(
        indicators_repository=_FakeRolIndicatorsRepository(),
        goals_repository=_FakeRolBranchCurveGoalsRepository(),
        calculator=StrategicIndicatorsCalculator(),
    )
    items = use_case.execute(
        source_keys=["commercial_rol"],
        start_date=start_date,
        end_date=end_date,
    )
    assert len(items) == 1
    return items[0]


def test_full_year_consolidated_equals_official_curve_total() -> None:
    """Ano completo: soma exata da curva (11,4M + 40,6M = 52M), nunca media x 12."""
    item = _execute(start_date="01-01-2026", end_date="31-12-2026")

    assert item["goal_mode"] == "monthly_curve"
    assert item["comparable_goal"] == pytest.approx(52_000_000.00, abs=0.005)
    assert item["comparable_goal"] != pytest.approx(51_999_999.96, abs=0.005)
    assert item["has_goal"] is True

    merged = _merged_monthly_targets()
    returned = {
        int(target["month_number"]): float(target["target_value"])
        for target in item["monthly_targets"]
    }
    assert returned == {
        int(target["month_number"]): float(target["target_value"])
        for target in merged
    }


def test_first_quarter_sums_integral_months_exactly() -> None:
    """Q1 = jan + fev + mar cadastrados (3.516M + 4.404M + 4.396M)."""
    item = _execute(start_date="01-01-2026", end_date="31-03-2026")

    assert item["comparable_goal"] == pytest.approx(12_316_000.00, abs=0.005)


def test_mixed_period_prorates_only_the_partial_month() -> None:
    """01/01-15/04: meses cheios integrais + fracao de abril da curva."""
    item = _execute(start_date="01-01-2026", end_date="15-04-2026")

    april_merged = 950_000.0 + 3_459_333.33
    expected = 12_316_000.00 + april_merged * (15 / 30)
    assert item["comparable_goal"] == pytest.approx(expected, abs=0.01)


def test_interval_inside_single_month_prorates_curve_value() -> None:
    item = _execute(start_date="10-01-2026", end_date="20-01-2026")

    january_merged = 950_000.0 + 2_566_000.0
    expected = january_merged * (11 / 31)
    assert item["comparable_goal"] == pytest.approx(expected, abs=0.01)


def test_explicit_full_month_dates_do_not_prorate() -> None:
    """01/02-28/02: valor integral de fevereiro, sem proporcionalizacao."""
    item = _execute(start_date="01-02-2026", end_date="28-02-2026")

    assert item["comparable_goal"] == pytest.approx(4_404_000.00, abs=0.005)


def test_reference_goal_remains_period_average_of_merged_curve() -> None:
    """Meta mes de referencia = media da curva consolidada no periodo."""
    item = _execute(start_date="01-01-2026", end_date="31-12-2026")

    assert item["reference_goal"] == pytest.approx(4_333_333.33, abs=0.01)
