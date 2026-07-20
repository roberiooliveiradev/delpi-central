from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicIndicatorCalculatedValue,
)
from si_app.application.use_cases.strategic_indicators.get_dashboard_indicator_metric_use_case import (
    GetDashboardIndicatorMetricUseCase,
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
