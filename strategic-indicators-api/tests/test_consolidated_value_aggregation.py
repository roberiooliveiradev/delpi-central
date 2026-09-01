from __future__ import annotations

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorCatalogItem,
    StrategicIndicatorMeasuredValue,
)
from si_app.domain.services.strategic_indicators_calculator import (
    StrategicIndicatorsCalculator,
)
from si_app.shared.consolidated_value_aggregation import (
    aggregate_branch_goal_values,
    aggregate_unit_branch_values,
    is_source_consolidated_mode,
    normalize_branch_value_aggregation,
    resolve_consolidated_value_aggregation,
)


def test_resolve_sum_from_explicit_mode() -> None:
    assert (
        resolve_consolidated_value_aggregation(branch_value_aggregation="sum")
        == "sum"
    )


def test_resolve_average_from_explicit_mode() -> None:
    assert (
        resolve_consolidated_value_aggregation(branch_value_aggregation="average")
        == "average"
    )


def test_auto_currency_defaults_to_sum() -> None:
    assert (
        resolve_consolidated_value_aggregation(
            branch_value_aggregation="auto",
            value_unit="currency",
        )
        == "sum"
    )


def test_auto_percent_defaults_to_average() -> None:
    assert (
        resolve_consolidated_value_aggregation(
            branch_value_aggregation="auto",
            value_unit="percent",
        )
        == "average"
    )


def test_aggregate_unit_branch_values_sum() -> None:
    assert aggregate_unit_branch_values(
        [614_974.68, 3_202_406.99],
        aggregation="sum",
    ) == 3_817_381.67


def test_branch_goal_values_never_sum_ppm() -> None:
    assert aggregate_branch_goal_values(
        [100.0, 200.0],
        branch_value_aggregation="sum",
        value_unit="ppm",
    ) == 150.0


def test_source_consolidated_mode_detection() -> None:
    assert is_source_consolidated_mode("source_consolidated")
    assert not is_source_consolidated_mode("sum")
    assert normalize_branch_value_aggregation(None) == "auto"


def test_branch_scoped_commercial_rol_realized_is_sum() -> None:
    calculator = StrategicIndicatorsCalculator()
    indicator = StrategicIndicatorCatalogItem(
        indicator_id="commercial-rol",
        department_id="commercial",
        indicator_name="ROL",
        weight_pct=40,
        goal_label="Curva",
        goal_value=0,
        goal_periodicity="monthly",
        goal_mode="monthly_curve",
        scope_type="per_unit",
        performance_direction="higher_is_better",
        value_unit="currency",
        branch_value_aggregation="sum",
        branch_goals={
            "01": {
                "goal_label": "01",
                "goal_value": 1_000_000,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [{"month_number": 5, "target_value": 1_000_000}],
            },
            "02": {
                "goal_label": "02",
                "goal_value": 2_000_000,
                "goal_periodicity": "monthly",
                "goal_mode": "monthly_curve",
                "monthly_targets": [{"month_number": 5, "target_value": 2_000_000}],
            },
        },
    )

    calculated = calculator.calculate_indicators(
        indicators_catalog=[indicator],
        measurements=[
            StrategicIndicatorMeasuredValue(
                indicator_id="commercial-rol",
                department_id="commercial",
                value=None,
                source="commercial_rol",
                unit_values={"01": 100.0, "02": 300.0},
            )
        ],
        competence="2026-05",
        start_date="01-05-2026",
        end_date="31-05-2026",
    )

    assert calculated[0].value == 400.0
