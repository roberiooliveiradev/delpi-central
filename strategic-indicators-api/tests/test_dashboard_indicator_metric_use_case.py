from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicIndicatorCalculatedValue,
    StrategicIndicatorCatalogItem,
)
from si_app.application.use_cases.strategic_indicators.get_dashboard_indicator_metric_use_case import (
    GetDashboardIndicatorMetricUseCase,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from tests.fixtures.si_goal_contract_cases import (
    CASE_A_EXACT,
    CASE_B_PARTIAL,
    CASE_B_PARTIAL_PPM,
    assert_triad_invariants,
)


def _indicator(**overrides) -> StrategicIndicatorCalculatedValue:
    base = dict(
        indicator_id="quality-ppm-internal",
        department_id="quality",
        indicator_name="PPM Interno",
        weight_pct=25.0,
        goal_label="Meta PPM",
        goal_value=100.0,
        goal_periodicity="monthly",
        goal_mode="standard",
        value=90.0,
        score=8.0,
        gap=-10.0,
        classification="Alto Desempenho",
        unit_values={"01": 90.0, "02": 90.0},
        value_unit="ppm",
        value_prefix=None,
        value_suffix=None,
        value_decimals=0,
    )
    base.update(overrides)
    return StrategicIndicatorCalculatedValue(**base)


def _department(
    *,
    indicators: list | None = None,
) -> StrategicDepartmentCalculatedValue:
    return StrategicDepartmentCalculatedValue(
        department_id="quality",
        department_name="Qualidade",
        short_name="Qualidade",
        weight_pct=15.0,
        strategic_summary="",
        aggregation_mode="average_of_units",
        score=7.25,
        contribution=1.2,
        classification="Alto Desempenho",
        trend="stable",
        indicators=indicators or [_indicator()],
    )


def _snapshot(*, departments: list) -> SimpleNamespace:
    return SimpleNamespace(
        current=SimpleNamespace(
            calculated_departments=departments,
            measurement_errors=[],
            period=SimpleNamespace(
                start_date="01-06-2026",
                end_date="30-06-2026",
                competence="2026-06",
            ),
        ),
        previous=None,
        catalog=SimpleNamespace(indicators_catalog=[]),
    )


def test_get_dashboard_indicator_realized_returns_value() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[_department()]
    )
    calculator = MagicMock()
    calculator.indicator_has_value.return_value = True
    calculator.build_realized_payload.return_value = {"01": 90.0, "02": 90.0}

    use_case = GetDashboardIndicatorMetricUseCase(
        snapshot_service=snapshot_service,
        calculator=calculator,
    )
    result = use_case.execute(
        indicator_id="quality-ppm-internal",
        kind="realized",
        competence="2026-06",
    )

    assert result is not None
    assert result["indicator_id"] == "quality-ppm-internal"
    assert result["value"] == 90.0
    assert result["has_value"] is True
    assert result["realized"] == {"01": 90.0, "02": 90.0}


def test_get_dashboard_indicator_meta_returns_comparable_goal() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[_department()]
    )
    calculator = MagicMock()
    calculator.resolve_goals_payload_for_calculated.return_value = {
        "01": 100.0,
        "02": 100.0,
    }
    calculator.calculate_comparable_goal.return_value = 100.0

    use_case = GetDashboardIndicatorMetricUseCase(
        snapshot_service=snapshot_service,
        calculator=calculator,
    )
    result = use_case.execute(
        indicator_id="quality-ppm-internal",
        kind="meta",
        competence="2026-06",
    )

    assert result is not None
    assert result["value"] == 100.0
    assert result["comparable_goal"] == 100.0
    assert result["goal_value"] == 100.0
    assert result["has_value"] is True


def test_get_dashboard_indicator_metric_returns_none_when_missing() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[]
    )
    use_case = GetDashboardIndicatorMetricUseCase(
        snapshot_service=snapshot_service,
        calculator=MagicMock(),
    )
    assert (
        use_case.execute(indicator_id="missing-indicator", kind="realized") is None
    )


def test_get_dashboard_indicator_meta_partial_keeps_registered_goal_value() -> None:
    """Mês parcial: goal_value cadastrado; value/comparable = prorata (Kaizen/TV)."""
    case = CASE_B_PARTIAL
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[
            _department(
                indicators=[
                    _indicator(
                        indicator_id="kaizen-ideas-per-month",
                        department_id="hr",
                        indicator_name="Ideias/mês",
                        goal_value=case["registered_goal_value"],
                        value_unit=case["value_unit"],
                        value=4.0,
                        unit_values={"01": 4.0},
                    )
                ]
            )
        ]
    )
    # Override period to partial August
    snap = snapshot_service.get_current_and_previous_snapshot.return_value
    snap.current.period = SimpleNamespace(
        start_date=case["start_date"],
        end_date=case["end_date"],
        competence=case["competence"],
    )

    use_case = GetDashboardIndicatorMetricUseCase(
        snapshot_service=snapshot_service,
        calculator=StrategicIndicatorsCalculator(),
    )
    result = use_case.execute(
        indicator_id="kaizen-ideas-per-month",
        kind="meta",
        start_date=case["start_date"],
        end_date=case["end_date"],
        competence=case["competence"],
    )

    assert result is not None
    assert_triad_invariants(case, result)
    assert result["goal_value"] == 8.0
    assert abs(float(result["comparable_goal"]) - 4.39) < 0.01
    assert result["value"] == result["comparable_goal"]
    assert result["reference_goal"] == 8.0


def test_get_dashboard_indicator_meta_partial_ppm_registered_not_prorata() -> None:
    case = CASE_B_PARTIAL_PPM
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[
            _department(
                indicators=[
                    _indicator(
                        goal_value=case["registered_goal_value"],
                        value_unit=case["value_unit"],
                        value=835.19,
                        unit_values={"01": 835.19},
                    )
                ]
            )
        ]
    )
    snap = snapshot_service.get_current_and_previous_snapshot.return_value
    snap.current.period = SimpleNamespace(
        start_date=case["start_date"],
        end_date=case["end_date"],
        competence=case["competence"],
    )

    use_case = GetDashboardIndicatorMetricUseCase(
        snapshot_service=snapshot_service,
        calculator=StrategicIndicatorsCalculator(),
    )
    result = use_case.execute(
        indicator_id="quality-ppm-internal",
        kind="meta",
        start_date=case["start_date"],
        end_date=case["end_date"],
        competence=case["competence"],
    )

    assert result is not None
    assert_triad_invariants(case, result)
    assert result["goal_value"] == 1400.0
    assert abs(float(result["comparable_goal"]) - round(1400.0 * 17 / 31, 2)) < 0.02


def test_get_dashboard_indicator_meta_exact_triad_equal() -> None:
    case = CASE_A_EXACT
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[
            _department(
                indicators=[
                    _indicator(
                        goal_value=case["registered_goal_value"],
                        value_unit=case["value_unit"],
                    )
                ]
            )
        ]
    )
    snap = snapshot_service.get_current_and_previous_snapshot.return_value
    snap.current.period = SimpleNamespace(
        start_date=case["start_date"],
        end_date=case["end_date"],
        competence=case["competence"],
    )

    use_case = GetDashboardIndicatorMetricUseCase(
        snapshot_service=snapshot_service,
        calculator=StrategicIndicatorsCalculator(),
    )
    result = use_case.execute(
        indicator_id="quality-ppm-internal",
        kind="meta",
        start_date=case["start_date"],
        end_date=case["end_date"],
        competence=case["competence"],
    )

    assert result is not None
    assert_triad_invariants(case, result)

def test_get_dashboard_indicator_meta_consolidated_monthly_curve_uses_rollup() -> None:
    """Visão consolidada: META MÊS = soma refs 01+02; PARCIAL = 1× MTD (não meta da 01)."""
    catalog_item = StrategicIndicatorCatalogItem(
        indicator_id="commercial-rol",
        department_id="commercial",
        indicator_name="ROL",
        weight_pct=20.0,
        goal_label="Curva R$",
        goal_value=0.0,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        monthly_targets=[],
        scope_type="per_unit",
        value_unit="currency",
        branch_value_aggregation="sum",
        branch_goals={
            "01": {
                "goal_value": 0.0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [
                    {"month_number": 9, "target_value": 1_160_000.0},
                ],
            },
            "02": {
                "goal_value": 0.0,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [
                    {"month_number": 9, "target_value": 3_614_000.0},
                ],
            },
        },
    )
    # calculated.goal_value simula cadastro "primário" só da 01 (bug antigo da TV).
    calculated = _indicator(
        indicator_id="commercial-rol",
        department_id="commercial",
        indicator_name="ROL",
        goal_label="Curva R$",
        goal_value=0.0,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        monthly_targets=[{"month_number": 9, "target_value": 1_160_000.0}],
        value_unit="currency",
        value=500_000.0,
        unit_values={"01": 200_000.0, "02": 300_000.0},
        branch_value_aggregation="sum",
    )
    snapshot_service = MagicMock()
    snap = _snapshot(departments=[_department(indicators=[calculated])])
    snap.catalog.indicators_catalog = [catalog_item]
    snap.current.period = SimpleNamespace(
        start_date="01-09-2026",
        end_date="04-09-2026",
        competence="2026-09",
    )
    snapshot_service.get_current_and_previous_snapshot.return_value = snap

    use_case = GetDashboardIndicatorMetricUseCase(
        snapshot_service=snapshot_service,
        calculator=StrategicIndicatorsCalculator(),
    )
    result = use_case.execute(
        indicator_id="commercial-rol",
        kind="meta",
        start_date="01-09-2026",
        end_date="04-09-2026",
        competence="2026-09",
        branch=None,
    )

    assert result is not None
    assert result["reference_goal"] == 4_774_000.0
    assert result["goal_value"] == 4_774_000.0
    assert result["comparable_goal"] == round(4_774_000.0 * 4 / 30, 2)
    # Não pode ser só a meta parcial da filial 01
    assert result["comparable_goal"] != round(1_160_000.0 * 4 / 30, 2)

