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


def test_reconcile_production_uses_average_of_units_not_indicator_average() -> None:
    """IDD consolidado = média dos IDDs 01/02, não média ponderada de notas já agregadas."""
    calculator = StrategicIndicatorsCalculator()
    catalog = [
        StrategicIndicatorCatalogItem(
            indicator_id="production-oee",
            department_id="production",
            indicator_name="OEE",
            weight_pct=100,
            goal_label="70%",
            goal_value=70.0,
            goal_periodicity="monthly",
            branch_goals={
                "01": {
                    "goal_value": 70.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
                "02": {
                    "goal_value": 70.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
            },
        ),
    ]
    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id="production-oee",
            department_id="production",
            value=80.0,
            source="test",
            unit_values={"01": 80.0, "02": 60.0},
        ),
    ]

    departments = calculator.calculate_departments(
        departments_catalog=[
            StrategicDepartmentCatalogItem(
                department_id="production",
                department_name="Produção",
                short_name="PRO",
                weight_pct=17,
                strategic_summary="",
                aggregation_mode="average_of_units",
            )
        ],
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )
    expected_score = departments[0].score
    assert expected_score > 0

    wrong_flat_average = StrategicIndicatorCalculatedValue(
        indicator_id="production-oee",
        department_id="production",
        indicator_name="OEE",
        weight_pct=100,
        goal_label="70%",
        goal_value=70.0,
        goal_periodicity="monthly",
        value=70.0,
        score=9.5,
        classification="Excelência Integrada",
    )
    stale_department = StrategicDepartmentCalculatedValue(
        department_id="production",
        department_name="Produção",
        short_name="PRO",
        weight_pct=17,
        strategic_summary="",
        aggregation_mode="average_of_units",
        score=9.5,
        contribution=1.62,
        classification="Excelência Integrada",
        trend="stable",
        indicators=[wrong_flat_average],
    )

    reconciled = calculator.reconcile_period_snapshot_departments(
        calculated_departments=[stale_department],
        calculated_indicators=[wrong_flat_average],
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )

    assert reconciled[0].score == expected_score
    assert reconciled[0].score != 9.5


def test_commercial_branch_view_matches_consolidated_scoring() -> None:
    calculator = StrategicIndicatorsCalculator()
    catalog = [
        StrategicIndicatorCatalogItem(
            indicator_id="commercial-closing-rate",
            department_id="commercial",
            indicator_name="Taxa de Fechamento",
            weight_pct=100,
            goal_label="10%",
            goal_value=10.0,
            goal_periodicity="monthly",
            scope_type="per_unit",
            has_resolved_goal=True,
            resolved_goal_scope_branch="01",
        ),
    ]
    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id="commercial-closing-rate",
            department_id="commercial",
            value=8.0,
            source="test",
            unit_values={"01": 5.0, "02": 9.0},
        ),
    ]
    department_catalog = [
        StrategicDepartmentCatalogItem(
            department_id="commercial",
            department_name="Comercial",
            short_name="COM",
            weight_pct=17,
            strategic_summary="",
            aggregation_mode="average_of_units",
        )
    ]

    consolidated = calculator.calculate_departments(
        departments_catalog=department_catalog,
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )
    branch_01 = calculator.calculate_departments(
        departments_catalog=department_catalog,
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
        scope_branch="01",
        precalculated_indicators=calculator.calculate_indicators(
            indicators_catalog=catalog,
            measurements=measurements,
            competence="2026-04",
            start_date="01-04-2026",
            end_date="30-04-2026",
            scope_branch="01",
        ),
    )

    assert consolidated[0].score > 0
    assert branch_01[0].score > 0
    # Comercial por unidade: consolidado = média 01/02; filial 01 ≠ consolidado quando 02 difere.
    assert branch_01[0].score != consolidated[0].score
