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
    build_purchase_order_detail_sql,
    build_purchase_orders_list_count_sql,
    build_purchase_orders_list_filters,
    build_purchase_orders_list_sql,
)
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_sql import (
    build_receipts_for_orders_sql,
)


def _delivery_status(expected_raw: str | None, *, today_protheus: str) -> str:
    value = (expected_raw or "").strip()
    if not value:
        return "no_date"
    if value < today_protheus:
        return "late"
    return "on_time"


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _receipt_item_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        str(row.get("branch") or "").strip(),
        str(row.get("order_number") or row.get("purchase_order_number") or "").strip(),
        str(row.get("order_item") or row.get("purchase_order_item") or "").strip(),
        str(row.get("supplier_code") or "").strip(),
        str(row.get("supplier_store") or "").strip(),
        str(row.get("product_code") or "").strip(),
    )


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


def _normalize_detail_item(row: dict[str, Any], *, today_protheus: str) -> dict[str, Any]:
    item = _normalize_row(row, today_protheus=today_protheus)
    item["buyer_code"] = _optional_text(row.get("buyer_code"))
    item["source_request_number"] = _optional_text(row.get("source_request_number"))
    item["source_request_item"] = _optional_text(row.get("source_request_item"))
    item["receipts"] = []
    return item


def _normalize_receipt_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "invoice_number": row.get("invoice_number"),
        "invoice_series": row.get("invoice_series"),
        "invoice_item": row.get("invoice_item"),
        "quantity": float(row.get("quantity") or 0),
        "unit_price": float(row.get("unit_price") or 0),
        "total_value": float(row.get("total_value") or 0),
        "invoice_issue_date": protheus_date_to_iso(row.get("invoice_issue_date")),
        "entry_date": protheus_date_to_iso(row.get("entry_date")),
    }


def compose_open_purchase_order(
    rows: list[dict[str, Any]],
    receipt_rows: list[dict[str, Any]],
    *,
    today_protheus: str,
) -> dict[str, Any] | None:
    """Aggregate open SC7 lines into one (branch, order_number) ficha."""
    if not rows:
        return None
    items = [_normalize_detail_item(row, today_protheus=today_protheus) for row in rows]
    receipts_by_item: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = {}
    for receipt_row in receipt_rows:
        key = _receipt_item_key(receipt_row)
        receipts_by_item.setdefault(key, []).append(_normalize_receipt_row(receipt_row))
    for item in items:
        item["receipts"] = receipts_by_item.get(_receipt_item_key(item), [])
    first = items[0]
    return {
        "branch": first["branch"],
        "order_number": first["order_number"],
        "items": items,
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

    def get_open_order(
        self,
        *,
        branch: str,
        order_number: str,
        reference: date | None = None,
    ) -> dict[str, Any] | None:
        where_clause, params = build_purchase_orders_list_filters(
            branch=branch,
            order_number=order_number,
            reference=reference,
        )
        detail_sql = build_purchase_order_detail_sql(where_clause=where_clause)
        today_protheus = (reference or date.today()).strftime("%Y%m%d")
        with self as repo:
            rows = repo.execute_query(detail_sql, tuple(params))
        if not rows:
            return None
        order_keys = [_receipt_item_key(row) for row in rows]
        receipts_sql, receipts_params = build_receipts_for_orders_sql(order_keys)
        receipt_rows: list[dict[str, Any]] = []
        if order_keys:
            with self as repo:
                receipt_rows = repo.execute_query(receipts_sql, tuple(receipts_params))
        return compose_open_purchase_order(
            rows,
            receipt_rows,
            today_protheus=today_protheus,
        )
