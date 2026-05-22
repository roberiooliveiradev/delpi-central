from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.shared.branch_filter import build_unit_values_for_consolidated_department


def test_build_unit_values_repeats_consolidated_on_branch_view() -> None:
    unit_values = build_unit_values_for_consolidated_department(
        consolidated_value=15_000.0,
        view_branch="02",
    )
    assert unit_values["consolidated"] == 15_000.0
    assert unit_values["02"] == 15_000.0


def test_engineering_branch_view_uses_full_consolidated_realized() -> None:
    calculator = StrategicIndicatorsCalculator()
    full_gain = 15_845.85
    catalog = [
        StrategicIndicatorCatalogItem(
            indicator_id="engineering-transforma-plus",
            department_id="engineering",
            indicator_name="Ganhos TRANSFORMA+",
            weight_pct=40,
            goal_label="R$ 15.000/mês",
            goal_value=15_000.0,
            goal_periodicity="monthly",
            scope_type="consolidated",
            has_resolved_goal=True,
            resolved_goal_scope_branch="",
        ),
    ]
    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id="engineering-transforma-plus",
            department_id="engineering",
            value=full_gain,
            source="transforma_mais",
            unit_values=build_unit_values_for_consolidated_department(
                consolidated_value=full_gain,
                view_branch="02",
            ),
        ),
    ]

    consolidated = calculator.calculate_indicators(
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )
    branch_02 = calculator.calculate_indicators(
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
        scope_branch="02",
    )

    assert consolidated[0].value == full_gain
    assert branch_02[0].value == full_gain
    assert branch_02[0].score == consolidated[0].score

    departments = calculator.calculate_departments(
        departments_catalog=[
            StrategicDepartmentCatalogItem(
                department_id="engineering",
                department_name="Engenharia",
                short_name="ENG",
                weight_pct=10,
                strategic_summary="",
                aggregation_mode="consolidated",
            )
        ],
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
        scope_branch="02",
        precalculated_indicators=branch_02,
    )

    assert departments[0].score == consolidated[0].score
