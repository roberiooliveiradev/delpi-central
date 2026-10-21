"""Row → DTO normalization for stock-inventory snapshot rows.

Self-contained helpers: this context must not import use-case internals
from sibling financeiro/supplies contexts (isolated snapshot-query
context, doc 49).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.dto.financeiro_stock_inventory.stock_inventory_response import (
    StockInventoryItem,
    StockInventoryTypeSummary,
    StockInventoryWarehouseSummary,
)


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _opt_str(value: Any) -> str | None:
    text = _as_str(value)
    return text if text else None


def _decimal_str(value: Any, places: str = "0.0000") -> str:
    if value is None or value == "":
        return "0.00"
    try:
        return str(Decimal(str(value)).quantize(Decimal(places)))
    except (InvalidOperation, ValueError):
        return "0.00"


def as_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def normalize_stock_item(row: dict) -> StockInventoryItem:
    return StockInventoryItem(
        productCode=_as_str(row.get("product_code")),
        description=_opt_str(row.get("description")),
        productType=_opt_str(row.get("product_type")),
        productGroup=_opt_str(row.get("product_group")),
        unit=_opt_str(row.get("unit")),
        warehouse=_opt_str(row.get("warehouse")),
        branchCode=_opt_str(row.get("branch_code")),
        historicalQuantity=_decimal_str(row.get("historical_quantity")),
        historicalStockValue=_decimal_str(row.get("historical_stock_value")),
    )


def normalize_type_summary(row: dict) -> StockInventoryTypeSummary:
    return StockInventoryTypeSummary(
        productType=_opt_str(row.get("product_type")),
        itemCount=as_int(row.get("item_count")),
        totalQuantity=_decimal_str(row.get("total_quantity")),
        totalStockValue=_decimal_str(row.get("total_stock_value")),
    )


def normalize_warehouse_summary(row: dict) -> StockInventoryWarehouseSummary:
    return StockInventoryWarehouseSummary(
        branchCode=_opt_str(row.get("branch_code")),
        warehouse=_opt_str(row.get("warehouse")),
        itemCount=as_int(row.get("item_count")),
        totalQuantity=_decimal_str(row.get("total_quantity")),
        totalStockValue=_decimal_str(row.get("total_stock_value")),
    )


def build_pagination(
    *, page: int, page_size: int, total_items: int
) -> dict[str, int | bool]:
    total_pages = (
        max((total_items + page_size - 1) // page_size, 1) if total_items else 1
    )
    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }
