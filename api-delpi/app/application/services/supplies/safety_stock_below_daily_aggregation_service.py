"""GLPI #1178: fotografia de estoque de segurança por filial, sem N+1 SQL.

Reusa os mesmos SB2/01+98+99, SBZ/BZ_ESTSEG, SC7 e conversões do
Estoque de Segurança. Não confunde este alerta com ruptura projetada.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from app.domain.services.supplies.safety_stock_classification_service import (
    STATUS_BELOW,
    classify_safety_stock_status,
    calculate_deficit_quantity,
)
from app.domain.services.supplies.safety_stock_purchase_coverage_service import (
    build_purchase_coverage,
    enrich_open_purchase_orders,
)
from app.domain.services.reports.safety_stock_shortage_30d_rules import VALID_BRANCHES

BR_TIMEZONE = ZoneInfo("America/Sao_Paulo")


class _SafetyStockReadPort(Protocol):
    def fetch_materials_for_projection_batch(self, **kwargs: Any) -> list[dict[str, Any]]: ...
    def fetch_open_purchase_orders_for_branch(self, *, branch: str) -> list[dict[str, Any]]: ...


def _as_of_date() -> date:
    return datetime.now(BR_TIMEZONE).date()


def _date_status(value: Any, today: date) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "without_date"
    try:
        day = date.fromisoformat(raw[:10])
    except ValueError:
        return "without_date"
    return "overdue" if day < today else "scheduled"


class SafetyStockBelowDailyAggregationService:
    """2 consultas batch no máximo, segregadas por filial; saldos não mesclados."""

    def __init__(self, repository: _SafetyStockReadPort) -> None:
        self._repository = repository

    def collect_rows(
        self, *, branch: str, as_of_date: date | None = None
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        if branch not in VALID_BRANCHES:
            raise ValueError("Filial obrigatória: informe 01 (SC) ou 02 (ES).")
        today = as_of_date or _as_of_date()
        materials = self._repository.fetch_materials_for_projection_batch(
            branch=branch,
            include_blocked=False,
            product_group=None,
            unit=None,
            search=None,
            include_without_safety_stock=False,
        )

        below: list[dict[str, Any]] = []
        for material in materials:
            code = str(material.get("product_code") or "").strip()
            available = float(material.get("available_stock") or 0)
            safety = float(material.get("safety_stock") or 0)
            if not code or classify_safety_stock_status(
                safety_stock=safety, available_stock=available
            ) != STATUS_BELOW:
                continue
            below.append(material)

        # Não consulta SC7 quando não há alertas; evita N+1 por produto.
        orders_by_product: dict[str, list[dict[str, Any]]] = defaultdict(list)
        if below:
            for order in self._repository.fetch_open_purchase_orders_for_branch(
                branch=branch
            ):
                code = str(order.get("product_code") or "").strip()
                if code:
                    orders_by_product[code].append(order)

        result: list[dict[str, Any]] = []
        counts = {"sufficient": 0, "partial": 0, "none": 0}
        for material in below:
            code = str(material["product_code"]).strip()
            unit = str(material.get("unit") or "").strip()
            balance = float(material.get("available_stock") or 0)
            safety = float(material.get("safety_stock") or 0)
            deficit = calculate_deficit_quantity(
                safety_stock=safety, available_stock=balance
            )
            enriched, totals = enrich_open_purchase_orders(
                orders=orders_by_product.get(code, []),
                primary_unit=unit,
                secondary_unit=material.get("secondary_unit"),
                conversion_factor=material.get("conversion_factor"),
                conversion_type=material.get("conversion_type"),
            )
            coverage = build_purchase_coverage(
                deficit_quantity=deficit,
                enriched_orders=enriched,
                coverage_totals=totals,
            )
            coverage_status = str(coverage["status"])
            counts[coverage_status] += 1

            orders: list[dict[str, Any]] = []
            for order in enriched:
                status = _date_status(order.get("expected_delivery_date"), today)
                converted = order.get("open_quantity_primary_unit")
                orders.append({
                    "order_number": str(order.get("order_number") or "").strip(),
                    "order_item": str(order.get("order_item") or "").strip(),
                    "supplier_name": str(order.get("supplier_name") or "").strip(),
                    "warehouse": str(order.get("warehouse") or "").strip(),
                    "open_quantity": float(order.get("open_quantity") or 0),
                    "order_unit": str(order.get("unit") or "").strip(),
                    "open_quantity_primary_unit": (
                        float(converted) if converted is not None else None
                    ),
                    "expected_delivery_date": (
                        str(order.get("expected_delivery_date") or "").strip() or None
                    ),
                    "delivery_status": status,
                    "coverage_eligible": bool(order.get("coverage_eligible")),
                })
            orders.sort(key=lambda order: (
                order["expected_delivery_date"] or "9999-99-99",
                order["order_number"], order["order_item"],
            ))
            eligible = [order for order in orders if order["coverage_eligible"]]
            overdue_count = sum(
                1 for order in eligible if order["delivery_status"] == "overdue"
            )
            no_date_count = sum(
                1 for order in eligible if order["delivery_status"] == "without_date"
            )
            warnings = list(coverage.get("warnings") or [])
            if overdue_count:
                warnings.append(
                    f"{overdue_count} pedido(s) com entrega prevista já vencida."
                )
            if no_date_count:
                warnings.append(
                    f"{no_date_count} pedido(s) sem data de entrega prevista."
                )
            result.append({
                "product_code": code,
                "product_description": str(
                    material.get("product_description") or ""
                ).strip(),
                "branch": branch,
                "unit": unit,
                "available_stock": balance,
                "safety_stock": safety,
                "deficit_quantity": deficit,
                "eligible_open_quantity": float(
                    coverage.get("eligible_open_quantity") or 0
                ),
                "projected_stock_after_orders": balance + float(
                    coverage.get("eligible_open_quantity") or 0
                ),
                "remaining_to_buy": float(coverage.get("remaining_to_buy") or 0),
                "coverage_status": coverage_status,
                "next_expected_delivery_date": coverage.get(
                    "next_expected_delivery_date"
                ),
                "open_order_count": len(orders),
                "eligible_order_count": len(eligible),
                "purchase_orders": orders,
                "warnings": warnings,
                "is_stockout": balance <= 0,
            })

        # A prioridade começa sem cobertura e, depois, com maior déficit.
        rank = {"none": 0, "partial": 1, "sufficient": 2}
        result.sort(key=lambda row: (
            rank[row["coverage_status"]],
            -float(row["deficit_quantity"]),
            row["product_code"],
        ))
        meta = {
            "branch": branch,
            "asOfDate": today.isoformat(),
            "warehouses": ["01", "98", "99"],
            "materialsScanned": len(materials),
            "alertCount": len(result),
            "stockoutCount": sum(1 for item in result if item["is_stockout"]),
            "coveredCount": counts["sufficient"],
            "partialCount": counts["partial"],
            "uncoveredCount": counts["none"],
            "coverageRule": "quantity_only",
            "deliveryDatesAreEstimates": True,
        }
        return result, meta
