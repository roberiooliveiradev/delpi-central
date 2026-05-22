from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCalculatedValue,
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCalculatedValue,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


def test_monthly_curve_without_targets_falls_back_to_goal_value() -> None:
    calculator = StrategicIndicatorsCalculator()

    comparable = calculator.calculate_comparable_goal(
        goal_value=1_000_000.0,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        monthly_targets=[],
        competence="2026-05",
    )

    assert comparable == 1_000_000.0


def test_commercial_department_scores_with_rol_and_standard_indicators() -> None:
    calculator = StrategicIndicatorsCalculator()
    catalog = [
        StrategicIndicatorCatalogItem(
            indicator_id="commercial-rol-matrix",
            department_id="commercial",
            indicator_name="ROL Matriz",
            weight_pct=25,
            goal_label="Curva mensal",
            goal_value=1_000_000.0,
            goal_periodicity="monthly",
            goal_mode="monthly_curve",
            monthly_targets=[{"month_number": 5, "target_value": 500_000.0}],
            scope_type="per_unit",
        ),
        StrategicIndicatorCatalogItem(
            indicator_id="commercial-closing-rate",
            department_id="commercial",
            indicator_name="Taxa de Fechamento",
            weight_pct=15,
            goal_label="10%",
            goal_value=10.0,
            goal_periodicity="monthly",
            goal_mode="standard",
            scope_type="consolidated",
        ),
    ]
    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id="commercial-rol-matrix",
            department_id="commercial",
            value=400_000.0,
            source="commercial_head_office_rol_target",
            unit_values={"matrix": 400_000.0},
        ),
        StrategicIndicatorMeasuredValue(
            indicator_id="commercial-closing-rate",
            department_id="commercial",
            value=12.0,
            source="commercial_sales_conversion_rate",
            unit_values={"consolidated": 12.0},
        ),
    ]

    calculated = calculator.calculate_indicators(
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-05",
        start_date="01-05-2026",
        end_date="31-05-2026",
    )

    assert all(item.score is not None and item.score > 0 for item in calculated)

    departments = calculator.calculate_departments(
        departments_catalog=[
            StrategicDepartmentCatalogItem(
                department_id="commercial",
                department_name="Comercial",
                short_name="COM",
                weight_pct=17,
                strategic_summary="",
                aggregation_mode="consolidated",
            )
        ],
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-05",
        start_date="01-05-2026",
        end_date="31-05-2026",
    )

    assert len(departments) == 1
    assert departments[0].score > 0


def test_production_null_measurement_is_not_scored_as_zero() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="production-oee",
        department_id="production",
        indicator_name="OEE",
        weight_pct=20,
        goal_label="70%",
        goal_value=70.0,
        goal_periodicity="monthly",
        goal_mode="standard",
        scope_type="consolidated",
    )

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[
            StrategicIndicatorMeasuredValue(
                indicator_id="production-oee",
                department_id="production",
                value=None,
                source="production_oee",
                unit_values={"consolidated": None},
            )
        ],
        competence="2026-05",
    )

    assert len(calculated) == 1
    assert calculated[0].value is None
    assert calculated[0].score is None
    assert calculated[0].classification == calculator.MISSING_VALUE_CLASSIFICATION


def test_reconcile_department_score_from_stale_zero_with_scored_indicators() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicators = [
        StrategicIndicatorCalculatedValue(
            indicator_id="commercial-rol-matrix",
            department_id="commercial",
            indicator_name="ROL Matriz",
            weight_pct=25,
            goal_label="Meta",
            goal_value=748_000.0,
            goal_periodicity="monthly",
            goal_mode="monthly_curve",
            value=656_697.11,
            score=8.78,
            gap=91_302.89,
            classification="Alto Desempenho",
            unit_values={"matrix": 656_697.11},
        ),
        StrategicIndicatorCalculatedValue(
            indicator_id="commercial-closing-rate",
            department_id="commercial",
            indicator_name="Taxa de Fechamento",
            weight_pct=15,
            goal_label="10%",
            goal_value=10.0,
            goal_periodicity="monthly",
            value=7.55,
            score=7.55,
            gap=2.45,
            classification="Satisfatório com Alertas",
            unit_values={"consolidated": 7.55},
        ),
    ]
    stale_department = StrategicDepartmentCalculatedValue(
        department_id="commercial",
        department_name="Comercial",
        short_name="COM",
        weight_pct=17,
        strategic_summary="",
        aggregation_mode="consolidated",
        score=0.0,
        contribution=0.0,
        classification="Crítico",
        trend="stable",
        indicators=indicators,
    )

    reconciled = calculator.reconcile_period_snapshot_departments(
        calculated_departments=[stale_department],
        calculated_indicators=indicators,
    )

    assert len(reconciled) == 1
    assert reconciled[0].score > 0
    assert reconciled[0].contribution > 0
    assert reconciled[0].classification != "Crítico"


def test_reconcile_uses_flat_indicators_when_nested_scores_are_missing() -> None:
    calculator = StrategicIndicatorsCalculator()
    scored = StrategicIndicatorCalculatedValue(
        indicator_id="commercial-rol-matrix",
        department_id="commercial",
        indicator_name="ROL Matriz",
        weight_pct=25,
        goal_label="Meta",
        goal_value=748_000.0,
        goal_periodicity="monthly",
        value=656_697.11,
        score=8.78,
    )
    stale_nested = StrategicIndicatorCalculatedValue(
        indicator_id="commercial-rol-matrix",
        department_id="commercial",
        indicator_name="ROL Matriz",
        weight_pct=25,
        goal_label="Meta",
        goal_value=748_000.0,
        goal_periodicity="monthly",
        value=656_697.11,
        score=None,
    )
    stale_department = StrategicDepartmentCalculatedValue(
        department_id="commercial",
        department_name="Comercial",
        short_name="COM",
        weight_pct=17,
        strategic_summary="",
        aggregation_mode="consolidated",
        score=0.0,
        contribution=0.0,
        classification="Crítico",
        trend="stable",
        indicators=[stale_nested],
    )

    reconciled = calculator.reconcile_period_snapshot_departments(
        calculated_departments=[stale_department],
        calculated_indicators=[scored],
    )

    assert reconciled[0].score == 8.78
