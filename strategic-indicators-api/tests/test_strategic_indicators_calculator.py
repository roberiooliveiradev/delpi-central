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


def test_missing_measurement_scores_zero_and_penalizes_department() -> None:
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
    assert calculated[0].score == 0.0
    assert calculated[0].classification == calculator.classify_score(0.0)


def test_catalog_indicator_without_measurement_scores_zero() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = _financial_fixed_cost_indicator()

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[],
    )

    assert len(calculated) == 1
    assert calculated[0].score == 0.0
    assert calculated[0].classification == calculator.classify_score(0.0)


def test_supplies_negotiation_savings_without_data_scores_zero() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="supplies_negotiation_savings",
        department_id="supplies",
        indicator_name="Economia em Negociações de Compras",
        weight_pct=15,
        goal_label="Meta",
        goal_value=100_000.0,
        goal_periodicity="monthly",
        goal_mode="standard",
        scope_type="per_unit",
        performance_direction="higher_is_better",
        branch_goals={
            "01": {
                "goal_value": 100_000.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
            "02": {
                "goal_value": 100_000.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "monthly_targets": [],
            },
        },
        has_resolved_goal=True,
    )

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[
            StrategicIndicatorMeasuredValue(
                indicator_id="supplies_negotiation_savings",
                department_id="supplies",
                value=None,
                source="supplies_negotiation_savings",
                unit_values={"01": None, "02": None},
            )
        ],
        competence="2026-05",
        start_date="01-05-2026",
        end_date="31-05-2026",
    )

    assert len(calculated) == 1
    assert calculated[0].value is None
    assert calculated[0].score == 0.0
    assert calculated[0].classification == calculator.classify_score(0.0)


def test_standard_closed_month_goal_unchanged() -> None:
    calculator = StrategicIndicatorsCalculator()
    comparable = calculator.calculate_comparable_goal(
        goal_value=310_000.0,
        goal_periodicity="monthly",
        start_date="01-05-2026",
        end_date="31-05-2026",
        competence="2026-05",
        value_unit="currency",
    )
    assert comparable == 310_000.0
    flags = calculator.resolve_goal_period_flags(
        start_date="01-05-2026",
        end_date="31-05-2026",
        competence="2026-05",
        value_unit="currency",
    )
    assert flags["goal_aggregation"] == "sum"
    assert flags["goal_period_partial"] is False


def test_standard_mtd_day_15_prorata() -> None:
    calculator = StrategicIndicatorsCalculator()
    # Maio tem 31 dias; 15/31 da meta mensal
    comparable = calculator.calculate_comparable_goal(
        goal_value=310_000.0,
        goal_periodicity="monthly",
        start_date="01-05-2026",
        end_date="15-05-2026",
        competence="2026-05",
        value_unit="currency",
    )
    assert comparable == 150_000.0
    flags = calculator.resolve_goal_period_flags(
        start_date="01-05-2026",
        end_date="15-05-2026",
        value_unit="currency",
    )
    assert flags["goal_period_partial"] is True
    assert flags["goal_aggregation"] == "sum"


def test_standard_ytd_partial_last_month() -> None:
    calculator = StrategicIndicatorsCalculator()
    # Jan–Abr fechados (4×100k) + Mai 15/31 × 100k
    comparable = calculator.calculate_comparable_goal(
        goal_value=100_000.0,
        goal_periodicity="monthly",
        start_date="01-01-2026",
        end_date="15-05-2026",
        value_unit="currency",
    )
    expected = 400_000.0 + round(100_000.0 * (15 / 31), 2)
    assert comparable == expected
    flags = calculator.resolve_goal_period_flags(
        start_date="01-01-2026",
        end_date="15-05-2026",
        value_unit="currency",
    )
    # Multi-mês: acumulada, sem parcial no rótulo
    assert flags["goal_period_partial"] is False


def test_percent_ytd_average_not_sum() -> None:
    calculator = StrategicIndicatorsCalculator()
    comparable = calculator.calculate_comparable_goal(
        goal_value=95.0,
        goal_periodicity="monthly",
        start_date="01-01-2026",
        end_date="15-08-2026",
        value_unit="percent",
        indicator_id="commercial-sales-order-otd",
    )
    assert comparable == 95.0
    flags = calculator.resolve_goal_period_flags(
        start_date="01-01-2026",
        end_date="15-08-2026",
        value_unit="percent",
        indicator_id="commercial-sales-order-otd",
    )
    assert flags["goal_aggregation"] == "average"
    assert flags["goal_period_partial"] is False


def test_percent_mtd_partial_keeps_level() -> None:
    calculator = StrategicIndicatorsCalculator()
    comparable = calculator.calculate_comparable_goal(
        goal_value=10.0,
        goal_periodicity="monthly",
        start_date="01-04-2026",
        end_date="15-04-2026",
        value_unit="percent",
    )
    assert comparable == 10.0
    flags = calculator.resolve_goal_period_flags(
        start_date="01-04-2026",
        end_date="15-04-2026",
        value_unit="percent",
    )
    assert flags["goal_aggregation"] == "average"
    assert flags["goal_period_partial"] is True


def test_standard_annual_periodicity_prorata() -> None:
    calculator = StrategicIndicatorsCalculator()
    # Meta anual 1_200_000 → 100_000/mês; 10 dias de junho (30 dias)
    comparable = calculator.calculate_comparable_goal(
        goal_value=1_200_000.0,
        goal_periodicity="annual",
        start_date="01-06-2026",
        end_date="10-06-2026",
        value_unit="currency",
    )
    assert comparable == round(100_000.0 * (10 / 30), 2)


def test_monthly_curve_partial_month_fraction() -> None:
    calculator = StrategicIndicatorsCalculator()
    comparable = calculator.calculate_comparable_goal(
        goal_value=0.0,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        monthly_targets=[{"month_number": 5, "target_value": 310_000.0}],
        start_date="01-05-2026",
        end_date="15-05-2026",
        competence="2026-05",
        value_unit="currency",
    )
    assert comparable == 150_000.0


def test_monthly_curve_percent_average_level() -> None:
    calculator = StrategicIndicatorsCalculator()
    comparable = calculator.calculate_comparable_goal(
        goal_value=0.0,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        monthly_targets=[
            {"month_number": 1, "target_value": 90.0},
            {"month_number": 2, "target_value": 90.0},
        ],
        start_date="01-01-2026",
        end_date="28-02-2026",
        value_unit="percent",
    )
    assert comparable == 90.0


def test_monthly_curve_closed_month_full_point() -> None:
    calculator = StrategicIndicatorsCalculator()
    comparable = calculator.calculate_comparable_goal(
        goal_value=0.0,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        monthly_targets=[{"month_number": 5, "target_value": 500_000.0}],
        start_date="01-05-2026",
        end_date="31-05-2026",
        competence="2026-05",
        value_unit="currency",
    )
    assert comparable == 500_000.0


def test_goal_prorata_anti_zero_guard() -> None:
    calculator = StrategicIndicatorsCalculator()
    comparable = calculator.calculate_comparable_goal(
        goal_value=0.01,
        goal_periodicity="monthly",
        start_date="01-02-2026",
        end_date="01-02-2026",
        value_unit="currency",
    )
    # 0.01 / 28 ≈ 0.000357 → round 0 → guard 0.01
    assert comparable == 0.01


def test_closed_month_score_parity_with_full_goal() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="commercial-closing-rate",
        department_id="commercial",
        indicator_name="Taxa",
        weight_pct=15,
        goal_label="10%",
        goal_value=10.0,
        goal_periodicity="monthly",
        scope_type="consolidated",
        performance_direction="higher_is_better",
        has_resolved_goal=True,
    )
    measurements = [
        StrategicIndicatorMeasuredValue(
            indicator_id="commercial-closing-rate",
            department_id="commercial",
            value=10.0,
            source="commercial_sales_conversion_rate",
        )
    ]
    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=measurements,
        competence="2026-04",
        start_date="01-04-2026",
        end_date="30-04-2026",
    )
    assert calculated[0].score == 10.0
