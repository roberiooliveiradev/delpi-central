from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)


def _financial_fixed_cost_indicator() -> StrategicIndicatorCatalogItem:
    return StrategicIndicatorCatalogItem(
        indicator_id="financial-fixed-cost",
        department_id="financial",
        indicator_name="Custos fixos",
        weight_pct=25,
        goal_label="Meta",
        goal_value=14.0,
        goal_periodicity="monthly",
        scope_type="consolidated",
        performance_direction="lower_is_better",
        strategic_description="",
        value_unit="percent",
        value_prefix=None,
        value_suffix="%",
        value_decimals=2,
    )


def test_lower_is_better_real_zero_scores_ten() -> None:
    calculator = StrategicIndicatorsCalculator()

    score = calculator.calculate_indicator_score(
        performance_direction="lower_is_better",
        comparable_goal=14.0,
        value=0.0,
    )

    assert score == 10.0


def test_missing_measurement_is_reported_without_score() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = _financial_fixed_cost_indicator()

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[
            StrategicIndicatorMeasuredValue(
                indicator_id=indicator.indicator_id,
                department_id=indicator.department_id,
                value=None,
                source="financial_fixed_cost",
                unit_values={"01": None, "02": 0.0},
            )
        ],
    )

    assert len(calculated) == 1
    assert calculated[0].value is None
    assert calculated[0].score is None
    assert calculated[0].classification == calculator.MISSING_VALUE_CLASSIFICATION


def test_catalog_indicator_without_measurement_is_reported() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = _financial_fixed_cost_indicator()

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[],
    )

    assert len(calculated) == 1
    assert calculated[0].classification == calculator.MISSING_VALUE_CLASSIFICATION
