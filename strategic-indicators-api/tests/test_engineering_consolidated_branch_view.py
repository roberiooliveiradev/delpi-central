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


def test_build_unit_values_keeps_consolidated_only_for_display() -> None:
    unit_values = build_unit_values_for_consolidated_department(
        consolidated_value=15_000.0,
        view_branch="02",
    )
    assert unit_values == {"consolidated": 15_000.0}


def test_build_realized_payload_strips_branch_keys_for_engineering() -> None:
    calculator = StrategicIndicatorsCalculator()
    realized = calculator.build_realized_payload(
        unit_values={"consolidated": 100.0, "02": 100.0},
        value=100.0,
        department_id="engineering",
    )
    assert realized == {"consolidated": 100.0}


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


def test_engineering_idd_not_zero_when_catalog_still_average_of_units() -> None:
    """
    Regressão: badge IDD 0.0 Crítico com notas dos KPIs em 10.

    Provider só publica unit_values.consolidated; average_of_units no catálogo
    (seed V009) zerava filiais 01/02. Calculador deve forçar consolidado.
    """
    calculator = StrategicIndicatorsCalculator()
    catalog = [
        StrategicIndicatorCatalogItem(
            indicator_id="engineering-projects-on-time",
            department_id="engineering",
            indicator_name="% LMP no prazo",
            weight_pct=60,
            goal_label="95%",
            goal_value=95.0,
            goal_periodicity="monthly",
            scope_type="per_unit",
            performance_direction="higher_is_better",
            has_resolved_goal=True,
            resolved_goal_scope_branch="",
        ),
        StrategicIndicatorCatalogItem(
            indicator_id="engineering-transforma-plus",
            department_id="engineering",
            indicator_name="Ganhos TRANSFORMA+",
            weight_pct=40,
            goal_label="R$ 15.000/mês",
            goal_value=15_000.0,
            goal_periodicity="monthly",
            scope_type="per_unit",
            performance_direction="higher_is_better",
            has_resolved_goal=True,
            resolved_goal_scope_branch="",
        ),
    ]
    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id="engineering-projects-on-time",
            department_id="engineering",
            value=100.0,
            source="lmp",
            unit_values=build_unit_values_for_consolidated_department(
                consolidated_value=100.0,
            ),
        ),
        StrategicIndicatorMeasuredValue(
            indicator_id="engineering-transforma-plus",
            department_id="engineering",
            value=16_817.57,
            source="transforma_mais",
            unit_values=build_unit_values_for_consolidated_department(
                consolidated_value=16_817.57,
            ),
        ),
    ]

    indicators = calculator.calculate_indicators(
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-07",
        start_date="01-07-2026",
        end_date="21-07-2026",
    )
    departments = calculator.calculate_departments(
        departments_catalog=[
            StrategicDepartmentCatalogItem(
                department_id="engineering",
                department_name="Engenharia",
                short_name="ENG",
                weight_pct=10,
                strategic_summary="",
                aggregation_mode="average_of_units",
            )
        ],
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-07",
        start_date="01-07-2026",
        end_date="21-07-2026",
        precalculated_indicators=indicators,
    )

    assert [item.score for item in indicators] == [10.0, 10.0]
    assert departments[0].score == 10.0
    assert departments[0].classification == "Excelência Integrada"


def test_engineering_ignores_orphan_branch_goals_with_consolidated_measurement() -> None:
    """Metas 01/02 sem realizado por filial não devem zerar nota em eng. consolidada."""
    calculator = StrategicIndicatorsCalculator()
    branch_goals = {
        "01": {
            "goal_value": 95.0,
            "goal_periodicity": "monthly",
            "goal_mode": "standard",
            "monthly_targets": [],
        },
        "02": {
            "goal_value": 95.0,
            "goal_periodicity": "monthly",
            "goal_mode": "standard",
            "monthly_targets": [],
        },
    }
    catalog = [
        StrategicIndicatorCatalogItem(
            indicator_id="engineering-projects-on-time",
            department_id="engineering",
            indicator_name="% LMP no prazo",
            weight_pct=100,
            goal_label="95%",
            goal_value=95.0,
            goal_periodicity="monthly",
            scope_type="per_unit",
            performance_direction="higher_is_better",
            has_resolved_goal=True,
            resolved_goal_scope_branch="",
            branch_goals=branch_goals,
        ),
    ]
    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id="engineering-projects-on-time",
            department_id="engineering",
            value=100.0,
            source="lmp",
            unit_values=build_unit_values_for_consolidated_department(
                consolidated_value=100.0,
            ),
        ),
    ]

    indicators = calculator.calculate_indicators(
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-07",
        start_date="01-07-2026",
        end_date="21-07-2026",
    )
    departments = calculator.calculate_departments(
        departments_catalog=[
            StrategicDepartmentCatalogItem(
                department_id="engineering",
                department_name="Engenharia",
                short_name="ENG",
                weight_pct=10,
                strategic_summary="",
                aggregation_mode="average_of_units",
            )
        ],
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-07",
        start_date="01-07-2026",
        end_date="21-07-2026",
        precalculated_indicators=indicators,
    )

    assert indicators[0].score == 10.0
    assert departments[0].score == 10.0
