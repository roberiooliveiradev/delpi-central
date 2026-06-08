from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicIndicatorCalculatedValue,
)
from si_app.application.use_cases.strategic_indicators.get_indicators_use_case import (
    GetStrategicIndicatorsUseCase,
)
from si_app.application.services.strategic_indicators.strategic_indicators_snapshot_models import (
    StrategicIndicatorsPeriodSnapshot,
)
from si_app.application.services.strategic_indicators.period_resolution import (
    ResolvedPeriod,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


def _indicator(
    *,
    indicator_id: str = "ind-1",
    score: float | None = 8.0,
) -> StrategicIndicatorCalculatedValue:
    return StrategicIndicatorCalculatedValue(
        indicator_id=indicator_id,
        department_id="dept-1",
        indicator_name="Indicador",
        weight_pct=10,
        goal_label="Meta",
        goal_value=100.0,
        goal_periodicity="monthly",
        scope_type="consolidated",
        performance_direction="higher_is_better",
        strategic_description="",
        value=90.0,
        score=score,
        gap=0.0,
        trend="stable",
        classification="Alto Desempenho",
        source="test",
    )


def _department(
    indicators: list[StrategicIndicatorCalculatedValue] | None = None,
) -> StrategicDepartmentCalculatedValue:
    return StrategicDepartmentCalculatedValue(
        department_id="dept-1",
        department_name="Departamento",
        short_name="DEP",
        weight_pct=10,
        strategic_summary="",
        aggregation_mode="consolidated",
        score=8.0,
        contribution=0.8,
        classification="Alto Desempenho",
        trend="stable",
        indicators=indicators or [],
    )


def _snapshot(
    *,
    competence: str,
    indicators: list[StrategicIndicatorCalculatedValue],
) -> StrategicIndicatorsPeriodSnapshot:
    department = _department(indicators)

    return StrategicIndicatorsPeriodSnapshot(
        period=ResolvedPeriod(
            competence=competence,
            start_date="01-04-2026",
            end_date="30-04-2026",
        ),
        measurements=[],
        measurement_errors=[],
        igd=8.0,
        igd_exact=8.0,
        classification="Alto Desempenho",
        calculated_departments=[department],
        calculated_indicators=indicators,
    )


def test_indicator_trend_uses_score_variation_between_periods() -> None:
    use_case = GetStrategicIndicatorsUseCase(
        snapshot_service=object(),  # type: ignore[arg-type]
        calculator=StrategicIndicatorsCalculator(),
    )

    current = _snapshot(
        competence="2026-04",
        indicators=[_indicator(score=8.5)],
    )
    previous = _snapshot(
        competence="2026-03",
        indicators=[_indicator(score=7.0)],
    )

    response = use_case.build_from_period_snapshot(current, previous_snapshot=previous)

    assert response.items[0].trend == "up"


def test_indicator_trend_is_stable_without_score() -> None:
    use_case = GetStrategicIndicatorsUseCase(
        snapshot_service=object(),  # type: ignore[arg-type]
        calculator=StrategicIndicatorsCalculator(),
    )

    current = _snapshot(
        competence="2026-04",
        indicators=[_indicator(score=None)],
    )

    response = use_case.build_from_period_snapshot(current, previous_snapshot=None)

    assert response.items[0].trend == "stable"
