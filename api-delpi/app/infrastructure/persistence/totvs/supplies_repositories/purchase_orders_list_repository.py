"""Repository — open purchase order lines (SC7) worklist."""

from __future__ import annotations

from datetime import date
from math import ceil
from typing import Any

from app.application.services.product.protheus_field_normalizer import protheus_date_to_iso
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pagination import paginate
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_orders_list_sql import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    build_purchase_orders_list_count_sql,
    build_purchase_orders_list_filters,
    build_purchase_orders_list_sql,
)


def _delivery_status(expected_raw: str | None, *, today_protheus: str) -> str:
    value = (expected_raw or "").strip()
    if not value:
        return "no_date"
    if value < today_protheus:
        return "late"
    return "on_time"


def _normalize_row(row: dict[str, Any], *, today_protheus: str) -> dict[str, Any]:
    expected_raw = row.get("expected_delivery_date")
    return {
        "branch": row.get("branch"),
        "order_number": row.get("order_number"),
        "order_item": row.get("order_item"),
        "product_code": row.get("product_code"),
        "product_description": row.get("product_description") or None,
        "ordered_quantity": float(row.get("ordered_quantity") or 0),
        "delivered_quantity": float(row.get("delivered_quantity") or 0),
        "open_quantity": float(row.get("open_quantity") or 0),
        "issue_date": protheus_date_to_iso(row.get("issue_date")),
        "expected_delivery_date": protheus_date_to_iso(expected_raw),
        "supplier_code": row.get("supplier_code"),
        "supplier_store": row.get("supplier_store"),
        "supplier_name": row.get("supplier_name") or None,
        "unit_price": float(row.get("unit_price") or 0),
        "open_value": float(row.get("open_value") or 0),
        "delivery_status": _delivery_status(expected_raw, today_protheus=today_protheus),
    }


class PurchaseOrdersListRepository(BaseRepository):
    def list_open_lines(
        self,
        *,
        branch: str,
        order_number: str | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        expected_delivery_from: str | None = None,
        expected_delivery_to: str | None = None,
        late_only: bool = False,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        reference: date | None = None,
    ) -> dict[str, Any]:
        safe_page = max(1, int(page or 1))
        safe_page_size = min(MAX_PAGE_SIZE, max(1, int(page_size or DEFAULT_PAGE_SIZE)))
        paging = paginate(safe_page, safe_page_size)
        where_clause, params = build_purchase_orders_list_filters(
            branch=branch,
            order_number=order_number,
            product_code=product_code,
            supplier_code=supplier_code,
            expected_delivery_from=expected_delivery_from,
            expected_delivery_to=expected_delivery_to,
            late_only=late_only,
            reference=reference,
        )
        count_sql = build_purchase_orders_list_count_sql(where_clause)
        list_sql = build_purchase_orders_list_sql(where_clause=where_clause)
        today_protheus = (reference or date.today()).strftime("%Y%m%d")
        with self as repo:
            total_row = repo.execute_one(count_sql, tuple(params))
            total = int(total_row["total"]) if total_row else 0
            rows = repo.execute_query(
                list_sql,
                tuple(params) + (paging["offset"], paging["page_size"]),
            )
        items = [
            _normalize_row(row, today_protheus=today_protheus) for row in rows
        ]
        total_pages = ceil(total / safe_page_size) if safe_page_size else 0
        return {
            "items": items,
            "page": safe_page,
            "page_size": safe_page_size,
            "total": total,
            "total_pages": total_pages,
        }
