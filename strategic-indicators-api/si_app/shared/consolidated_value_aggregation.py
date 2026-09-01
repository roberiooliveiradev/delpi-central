from __future__ import annotations

from typing import Literal

BranchValueAggregationMode = Literal[
    "auto",
    "sum",
    "average",
    "source_consolidated",
]
ConsolidatedValueAggregation = Literal["sum", "average"]

_BRANCH_VALUE_AGGREGATION_VALUES = frozenset(
    {"auto", "sum", "average", "source_consolidated"},
)

_VALUE_UNIT_DEFAULT: dict[str, ConsolidatedValueAggregation] = {
    "currency": "sum",
    "count": "sum",
}

_NON_SUMMABLE_VALUE_UNITS = frozenset({"percent", "ppm", "ratio"})


def normalize_branch_value_aggregation(
    value: str | None,
) -> BranchValueAggregationMode:
    normalized = (value or "auto").strip().lower()
    if normalized in _BRANCH_VALUE_AGGREGATION_VALUES:
        return normalized  # type: ignore[return-value]
    return "auto"


def is_source_consolidated_mode(
    branch_value_aggregation: str | None,
) -> bool:
    return normalize_branch_value_aggregation(branch_value_aggregation) == "source_consolidated"


def resolve_consolidated_value_aggregation(
    *,
    branch_value_aggregation: str | None = None,
    indicator_id: str | None = None,
    value_unit: str | None = None,
) -> ConsolidatedValueAggregation:
    _ = indicator_id
    mode = normalize_branch_value_aggregation(branch_value_aggregation)
    if mode == "sum":
        return "sum"
    if mode == "average":
        return "average"
    if mode == "source_consolidated":
        return "average"

    unit = (value_unit or "").strip().lower()
    return _VALUE_UNIT_DEFAULT.get(unit, "average")


def aggregate_unit_branch_values(
    values: list[float],
    *,
    aggregation: ConsolidatedValueAggregation,
) -> float | None:
    if not values:
        return None
    if aggregation == "sum":
        return round(sum(values), 2)
    return round(sum(values) / len(values), 2)


def aggregate_branch_goal_values(
    values: list[float],
    *,
    branch_value_aggregation: str | None,
    value_unit: str | None = None,
) -> float | None:
    unit = (value_unit or "").strip().lower()
    if unit in _NON_SUMMABLE_VALUE_UNITS:
        return aggregate_unit_branch_values(values, aggregation="average")

    aggregation = resolve_consolidated_value_aggregation(
        branch_value_aggregation=branch_value_aggregation,
        value_unit=value_unit,
    )
    return aggregate_unit_branch_values(values, aggregation=aggregation)
