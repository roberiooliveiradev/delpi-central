from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
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
