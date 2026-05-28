from __future__ import annotations

from typing import Literal

ConsolidatedValueAggregation = Literal["sum", "average"]

# Visão consolidada do realizado (quando há unit_values 01/02).
# A nota do indicador no SI continua sendo a média das notas por filial
# (departamento comercial: average_of_units).
INDICATOR_CONSOLIDATED_VALUE_AGGREGATION: dict[str, ConsolidatedValueAggregation] = {
    "commercial-rol": "sum",
    "commercial-closing-rate": "average",
    "commercial-sales-order-otd": "average",
    "commercial-new-business-rol": "average",
}

_VALUE_UNIT_DEFAULT: dict[str, ConsolidatedValueAggregation] = {
    "currency": "sum",
    "count": "sum",
}


def resolve_consolidated_value_aggregation(
    *,
    indicator_id: str,
    value_unit: str | None = None,
) -> ConsolidatedValueAggregation:
    explicit = INDICATOR_CONSOLIDATED_VALUE_AGGREGATION.get(indicator_id.strip())
    if explicit:
        return explicit

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
