from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicIndicatorCalculatedValue,
)
from si_app.application.use_cases.strategic_indicators.get_dashboard_department_indicators_use_case import (
    GetDashboardDepartmentIndicatorsUseCase,
)
from si_app.application.use_cases.strategic_indicators.get_dashboard_departments_indicators_use_case import (
    GetDashboardDepartmentsIndicatorsUseCase,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from tests.fixtures.si_goal_contract_cases import CASE_B_PARTIAL


def _indicator(**overrides) -> StrategicIndicatorCalculatedValue:
    base = dict(
        indicator_id="quality.ppm",
        department_id="quality",
        indicator_name="PPM",
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
    )
    base.update(overrides)
    return StrategicIndicatorCalculatedValue(**base)


def _department(
    *,
    department_id: str = "quality",
    score: float = 7.25,
    indicators: list | None = None,
) -> StrategicDepartmentCalculatedValue:
    return StrategicDepartmentCalculatedValue(
        department_id=department_id,
        department_name="Qualidade",
        short_name="Qualidade",
        weight_pct=15.0,
        strategic_summary="",
        aggregation_mode="average_of_units",
        score=score,
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


def test_get_dashboard_department_indicators_returns_idd_goals_realized() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[_department()]
    )
    calculator = MagicMock()
    calculator.indicator_has_value.return_value = True
    calculator.build_realized_payload.return_value = {"01": 90.0, "02": 90.0}
    calculator.resolve_goals_payload_for_calculated.return_value = {
        "01": 100.0,
        "02": 100.0,
    }

    use_case = GetDashboardDepartmentIndicatorsUseCase(
        snapshot_service=snapshot_service,
        calculator=calculator,
    )
    result = use_case.execute(
        department_id="quality",
        competence="2026-06",
        branch="01",
    )

    assert result is not None
    assert result["department_id"] == "quality"
    assert result["idd"] == 7.25
    assert result["score"] == 7.25
    assert len(result["indicators"]) == 1
    indicator = result["indicators"][0]
    assert indicator["indicator_id"] == "quality.ppm"
    assert indicator["realized"] == {"01": 90.0, "02": 90.0}
    assert indicator["goals"] == {"01": 100.0, "02": 100.0}
    assert indicator["value"] == 90.0
    assert indicator["goal_value"] == 100.0


def test_get_dashboard_department_indicators_returns_none_when_missing() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[]
    )
    use_case = GetDashboardDepartmentIndicatorsUseCase(
        snapshot_service=snapshot_service,
        calculator=MagicMock(),
    )
    assert use_case.execute(department_id="hr") is None


def test_get_dashboard_departments_indicators_lists_all() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[
            _department(department_id="quality", score=7.0),
            _department(
                department_id="commercial",
                score=8.0,
                indicators=[
                    _indicator(
                        indicator_id="commercial.otd",
                        department_id="commercial",
                        indicator_name="OTD",
                    )
                ],
            ),
        ]
    )
    calculator = MagicMock()
    calculator.indicator_has_value.return_value = True
    calculator.build_realized_payload.return_value = {"consolidated": 1.0}
    calculator.resolve_goals_payload_for_calculated.return_value = {
        "consolidated": 2.0
    }

    use_case = GetDashboardDepartmentsIndicatorsUseCase(
        snapshot_service=snapshot_service,
        calculator=calculator,
    )
    result = use_case.execute(competence="2026-06")

    assert len(result["items"]) == 2
    assert {item["department_id"] for item in result["items"]} == {
        "quality",
        "commercial",
    }
    assert all("idd" in item for item in result["items"])
    assert all(isinstance(item["indicators"], list) for item in result["items"])


def test_get_dashboard_departments_indicators_filters_department() -> None:
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[
            _department(department_id="quality"),
            _department(department_id="commercial"),
        ]
    )
    calculator = MagicMock()
    calculator.indicator_has_value.return_value = True
    calculator.build_realized_payload.return_value = {}
    calculator.resolve_goals_payload_for_calculated.return_value = {}

    use_case = GetDashboardDepartmentsIndicatorsUseCase(
        snapshot_service=snapshot_service,
        calculator=calculator,
    )
    result = use_case.execute(department_id="commercial")

    assert len(result["items"]) == 1
    assert result["items"][0]["department_id"] == "commercial"


def test_department_indicators_partial_goal_value_differs_from_goals_map() -> None:
    """goal_value cadastrado ≠ valores em goals (comparable do período)."""
    case = CASE_B_PARTIAL
    snapshot_service = MagicMock()
    snapshot_service.get_current_and_previous_snapshot.return_value = _snapshot(
        departments=[
            _department(
                indicators=[
                    _indicator(
                        indicator_id="kaizen-ideas",
                        goal_value=case["registered_goal_value"],
                        value_unit=case["value_unit"],
                        value=4.0,
                        unit_values={"01": 4.0, "02": 4.0},
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

    use_case = GetDashboardDepartmentIndicatorsUseCase(
        snapshot_service=snapshot_service,
        calculator=StrategicIndicatorsCalculator(),
    )
    result = use_case.execute(
        department_id="quality",
        start_date=case["start_date"],
        end_date=case["end_date"],
        competence=case["competence"],
    )

    assert result is not None
    indicator = result["indicators"][0]
    assert indicator["goal_value"] == case["expected_goal_value"]
    goals = indicator["goals"] or {}
    comparable_values = [float(v) for v in goals.values() if v is not None]
    assert comparable_values, "goals map must expose period comparable"
    assert all(
        abs(v - case["expected_comparable_goal"]) < 0.02 for v in comparable_values
    )
    assert all(v != indicator["goal_value"] for v in comparable_values)
