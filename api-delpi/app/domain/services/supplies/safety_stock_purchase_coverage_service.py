"""Cobertura do déficit físico por pedidos de compra em aberto (SC7)."""

from __future__ import annotations

from typing import Any

from app.domain.services.supplies.safety_stock_classification_service import (
    AVAILABLE_BALANCE_WAREHOUSES,
    TOLERANCE,
)
from app.domain.services.supplies.safety_stock_unit_conversion_service import (
    convert_quantity_to_primary_unit,
)

COVERAGE_SUFFICIENT = "sufficient"
COVERAGE_PARTIAL = "partial"
COVERAGE_NONE = "none"

ALLOWED_COVERAGE_STATUSES = frozenset(
    {
        COVERAGE_SUFFICIENT,
        COVERAGE_PARTIAL,
        COVERAGE_NONE,
    }
)


def is_coverage_eligible_warehouse(warehouse: str | None) -> bool:
    return str(warehouse or "").strip() in AVAILABLE_BALANCE_WAREHOUSES


def classify_purchase_coverage(
    *,
    deficit_quantity: float,
    eligible_open_quantity: float,
) -> str:
    deficit = max(float(deficit_quantity or 0), 0.0)
    open_qty = max(float(eligible_open_quantity or 0), 0.0)

    if deficit <= TOLERANCE:
        if open_qty > TOLERANCE:
            return COVERAGE_SUFFICIENT
        return COVERAGE_NONE
    if open_qty + TOLERANCE >= deficit:
        return COVERAGE_SUFFICIENT
    if open_qty > TOLERANCE:
        return COVERAGE_PARTIAL
    return COVERAGE_NONE


def remaining_to_buy(*, deficit_quantity: float, eligible_open_quantity: float) -> float:
    deficit = max(float(deficit_quantity or 0), 0.0)
    open_qty = max(float(eligible_open_quantity or 0), 0.0)
    return max(deficit - open_qty, 0.0)


def enrich_open_purchase_orders(
    *,
    orders: list[dict[str, Any]],
    primary_unit: str | None,
    secondary_unit: str | None,
    conversion_factor: float | int | str | None,
    conversion_type: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Normaliza pedidos e calcula cobertura elegível (armazéns 01/98/99 + UM compatível)."""
    enriched: list[dict[str, Any]] = []
    eligible_total = 0.0
    incompatible_count = 0
    next_delivery: str | None = None
    warnings: list[str] = []

    for raw in orders:
        warehouse = str(raw.get("warehouse") or "").strip()
        order_unit = str(raw.get("unit") or "").strip()
        open_qty = float(raw.get("open_quantity") or 0)
        conversion = convert_quantity_to_primary_unit(
            quantity=open_qty,
            source_unit=order_unit,
            primary_unit=primary_unit,
            secondary_unit=secondary_unit,
            conversion_factor=conversion_factor,
            conversion_type=conversion_type,
        )
        warehouse_eligible = is_coverage_eligible_warehouse(warehouse)
        converted = conversion.quantity if conversion.compatible else None
        coverage_eligible = bool(
            warehouse_eligible and conversion.compatible and (converted or 0) > 0
        )

        if conversion.compatible and converted is not None and warehouse_eligible:
            eligible_total += converted
        elif not conversion.compatible:
            incompatible_count += 1

        delivery = str(raw.get("expected_delivery_date") or "").strip() or None
        if coverage_eligible and delivery:
            if next_delivery is None or delivery < next_delivery:
                next_delivery = delivery

        enriched.append(
            {
                **raw,
                "warehouse": warehouse,
                "unit": order_unit,
                "open_quantity": open_qty,
                "open_quantity_primary_unit": converted,
                "unit_compatible": conversion.compatible,
                "unit_conversion_reason": conversion.reason,
                "warehouse_eligible": warehouse_eligible,
                "coverage_eligible": coverage_eligible,
            }
        )

    if incompatible_count:
        warnings.append(
            "Alguns pedidos usam unidade incompatível com o cadastro do produto "
            "e não entram na cobertura do déficit."
        )

    return enriched, {
        "eligible_open_quantity": eligible_total,
        "next_expected_delivery_date": next_delivery,
        "incompatible_unit_order_count": incompatible_count,
        "warnings": warnings,
    }


def build_purchase_coverage(
    *,
    deficit_quantity: float,
    enriched_orders: list[dict[str, Any]],
    coverage_totals: dict[str, Any],
) -> dict[str, Any]:
    eligible = float(coverage_totals.get("eligible_open_quantity") or 0)
    status = classify_purchase_coverage(
        deficit_quantity=deficit_quantity,
        eligible_open_quantity=eligible,
    )
    return {
        "status": status,
        "deficit_quantity": max(float(deficit_quantity or 0), 0.0),
        "eligible_open_quantity": eligible,
        "remaining_to_buy": remaining_to_buy(
            deficit_quantity=deficit_quantity,
            eligible_open_quantity=eligible,
        ),
        "open_order_count": len(enriched_orders),
        "eligible_order_count": sum(
            1 for order in enriched_orders if order.get("coverage_eligible")
        ),
        "next_expected_delivery_date": coverage_totals.get("next_expected_delivery_date"),
        "incompatible_unit_order_count": int(
            coverage_totals.get("incompatible_unit_order_count") or 0
        ),
        "warnings": list(coverage_totals.get("warnings") or []),
    }
