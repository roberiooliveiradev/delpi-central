from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.shared.branch_scoped_goals import (
    format_branch_scoped_goal_label,
    pick_primary_branch_goal,
)


def test_format_branch_scoped_goal_label() -> None:
    label = format_branch_scoped_goal_label(
        {
            "02": {"goal_label": "8 PDIs"},
            "01": {"goal_label": "15 PDIs"},
        }
    )

    assert label == "Un. 01: 15 PDIs | Un. 02: 8 PDIs"


def test_pick_primary_branch_goal_prefers_filial_01() -> None:
    goal = pick_primary_branch_goal(
        {
            "02": {"goal_value": 8.0},
            "01": {"goal_value": 15.0},
        }
    )

    assert goal["goal_value"] == 15.0


def test_consolidated_score_averages_branch_scores() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="hr-pdi",
        department_id="hr",
        indicator_name="PDIs ativos",
        weight_pct=10,
        goal_label="Un. 01: 15 | Un. 02: 8",
        goal_value=15,
        goal_periodicity="monthly",
        scope_type="consolidated",
        performance_direction="higher_is_better",
        branch_goals={
            "01": {
                "goal_label": "15",
                "goal_value": 15.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
            "02": {
                "goal_label": "8",
                "goal_value": 8.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
        },
    )

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[
            StrategicIndicatorMeasuredValue(
                indicator_id="hr-pdi",
                department_id="hr",
                value=9.5,
                source="portal_rh_pdi_count",
                unit_values={"01": 10.0, "02": 9.0},
            )
        ],
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )

    assert len(calculated) == 1
    assert calculated[0].score is not None
    assert calculated[0].score > 0
    assert calculated[0].classification != calculator.MISSING_VALUE_CLASSIFICATION


def test_department_consolidated_score_is_average_of_branch_idds() -> None:
    calculator = StrategicIndicatorsCalculator()
    catalog = [
        StrategicIndicatorCatalogItem(
            indicator_id="hr-pdi",
            department_id="hr",
            indicator_name="PDIs",
            weight_pct=50,
            goal_label="por unidade",
            goal_value=15,
            goal_periodicity="monthly",
            branch_goals={
                "01": {
                    "goal_value": 10.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
                "02": {
                    "goal_value": 10.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
            },
        ),
        StrategicIndicatorCatalogItem(
            indicator_id="hr-turnover",
            department_id="hr",
            indicator_name="Turnover",
            weight_pct=50,
            goal_label="por unidade",
            goal_value=5,
            goal_periodicity="monthly",
            performance_direction="lower_is_better",
            branch_goals={
                "01": {
                    "goal_value": 5.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
                "02": {
                    "goal_value": 5.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
            },
        ),
    ]
    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id="hr-pdi",
            department_id="hr",
            value=10.0,
            source="test",
            unit_values={"01": 10.0, "02": 5.0},
        ),
        StrategicIndicatorMeasuredValue(
            indicator_id="hr-turnover",
            department_id="hr",
            value=2.5,
            source="test",
            unit_values={"01": 0.0, "02": 5.0},
        ),
    ]

    departments = calculator.calculate_departments(
        departments_catalog=[
            StrategicDepartmentCatalogItem(
                department_id="hr",
                department_name="RH",
                short_name="RH",
                weight_pct=15,
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

    assert len(departments) == 1

    # Filial 01: PDI 10 + Turnover 10 → IDD 10 | Filial 02: PDI 5 + Turnover 10 → IDD 7,5
    assert departments[0].score == 8.75

    calculated = calculator.calculate_indicators(
        indicators_catalog=catalog,
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )
    assert calculated[0].unit_gaps == {"01": 0.0, "02": 5.0}
