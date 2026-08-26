"""Repository — purchase request lines (SC1 + SC7 + SD1)."""

from __future__ import annotations

from math import ceil
from typing import Any

from app.application.services.product.protheus_field_normalizer import protheus_date_to_iso
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pagination import paginate
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_lines_sql import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    build_purchase_orders_for_lines_sql,
    build_purchase_request_headers_count_sql,
    build_purchase_request_headers_page_sql,
    build_purchase_request_lines_filters,
    build_purchase_request_lines_for_request_numbers_sql,
    build_purchase_request_lines_list_sql,
    build_purchase_request_requesters_sql,
    build_receipts_for_orders_sql,
)


def _map_approval_status(raw: str | None) -> str:
    value = (raw or "").strip().upper()
    if value == "L":
        return "approved"
    if value == "R":
        return "rejected"
    if value == "B":
        return "blocked"
    return "unknown"


def _normalize_line_row(row: dict[str, Any]) -> dict[str, Any]:
    buyer_code = (row.get("buyer_code") or "").strip()
    return {
        "branch": row.get("branch"),
        "request_number": row.get("request_number"),
        "request_item": row.get("request_item"),
        "product_code": row.get("product_code"),
        "product_description": row.get("product_description") or None,
        "unit": row.get("unit") or None,
        "requested_quantity": float(row.get("requested_quantity") or 0),
        "ordered_quantity": float(row.get("ordered_quantity") or 0),
        "request_open_quantity": float(row.get("request_open_quantity") or 0),
        "request_issue_date": protheus_date_to_iso(row.get("request_issue_date")),
        "request_required_date": protheus_date_to_iso(row.get("request_required_date")),
        "requester_protheus_user_id": row.get("requester_protheus_user_id"),
        "requester_code": row.get("requester_code") or None,
        "requester_name": row.get("requester_name") or None,
        "cost_center_code": row.get("cost_center_code") or None,
        "cost_center_description": row.get("cost_center_description") or None,
        "account_code": row.get("account_code") or None,
        "approval_raw": row.get("approval_raw") or "",
        "approval_status": _map_approval_status(row.get("approval_raw")),
        "approver_name": row.get("approver_name") or None,
        "residual": bool(row.get("residual")),
        "suggested_supplier_code": row.get("suggested_supplier_code") or None,
        "suggested_supplier_store": row.get("suggested_supplier_store") or None,
        "suggested_supplier_name": row.get("suggested_supplier_name") or None,
        "purchase_orders": [],
    }


def _normalize_order_row(row: dict[str, Any]) -> dict[str, Any]:
    buyer_code = (row.get("buyer_code") or "").strip()
    return {
        "branch": row.get("branch"),
        "order_number": row.get("order_number"),
        "order_item": row.get("order_item"),
        "source_request_number": row.get("source_request_number"),
        "source_request_item": row.get("source_request_item"),
        "product_code": row.get("product_code"),
        "product_description": row.get("product_description") or None,
        "ordered_quantity": float(row.get("ordered_quantity") or 0),
        "received_quantity": float(row.get("received_quantity") or 0),
        "open_quantity": float(row.get("open_quantity") or 0),
        "issue_date": protheus_date_to_iso(row.get("issue_date")),
        "expected_delivery_date": protheus_date_to_iso(row.get("expected_delivery_date")),
        "supplier_code": row.get("supplier_code"),
        "supplier_store": row.get("supplier_store"),
        "supplier_name": row.get("supplier_name") or None,
        "buyer": {"code": buyer_code} if buyer_code else None,
        "order_user": {
            "protheus_user_id": row.get("order_user_protheus_user_id") or None,
            "code": row.get("order_user_code") or None,
            "name": row.get("order_user_name") or None,
        },
        "residual": bool(row.get("residual")),
        "receipts": [],
    }


def _normalize_receipt_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch": row.get("branch"),
        "invoice_number": row.get("invoice_number"),
        "invoice_series": row.get("invoice_series"),
        "invoice_item": row.get("invoice_item"),
        "purchase_order_number": row.get("purchase_order_number"),
        "purchase_order_item": row.get("purchase_order_item"),
        "product_code": row.get("product_code"),
        "supplier_code": row.get("supplier_code"),
        "supplier_store": row.get("supplier_store"),
        "quantity": float(row.get("quantity") or 0),
        "unit_price": float(row.get("unit_price") or 0),
        "total_value": float(row.get("total_value") or 0),
        "invoice_issue_date": protheus_date_to_iso(row.get("invoice_issue_date")),
        "entry_date": protheus_date_to_iso(row.get("entry_date")),
    }


class PurchaseRequestLinesRepository(BaseRepository):
    def list_lines(
        self,
        *,
        branch: str,
        date_from: str | None = None,
        date_to: str | None = None,
        cost_centers: list[str] | None = None,
        request_number: str | None = None,
        requester_protheus_user_ids: list[str] | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        order_number: str | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:
        safe_page = max(1, int(page or 1))
        safe_page_size = min(MAX_PAGE_SIZE, max(1, int(page_size or DEFAULT_PAGE_SIZE)))
        paging = paginate(safe_page, safe_page_size)
        where_clause, params = build_purchase_request_lines_filters(
            branch=branch,
            date_from=date_from,
            date_to=date_to,
            cost_centers=cost_centers,
            request_number=request_number,
            requester_protheus_user_ids=requester_protheus_user_ids,
            product_code=product_code,
            supplier_code=supplier_code,
            order_number=order_number,
        )
        count_sql = build_purchase_request_headers_count_sql(where_clause)
        headers_sql = build_purchase_request_headers_page_sql(where_clause=where_clause)
        with self as repo:
            total_row = repo.execute_one(count_sql, tuple(params))
            total = int(total_row["total"]) if total_row else 0
            header_rows = repo.execute_query(
                headers_sql,
                tuple(params) + (paging["offset"], paging["page_size"]),
            )
            request_numbers = [
                str(row.get("request_number") or "").strip()
                for row in header_rows
                if str(row.get("request_number") or "").strip()
            ]
            if request_numbers:
                lines_sql, lines_extra_params = build_purchase_request_lines_for_request_numbers_sql(
                    where_clause=where_clause,
                    request_numbers=request_numbers,
                )
                rows = repo.execute_query(lines_sql, tuple(params) + tuple(lines_extra_params))
            else:
                rows = []
        lines = [_normalize_line_row(row) for row in rows]
        self._attach_orders_and_receipts(lines)
        total_pages = ceil(total / safe_page_size) if safe_page_size else 0
        return {
            "items": lines,
            "page": safe_page,
            "page_size": safe_page_size,
            "total": total,
            "total_pages": total_pages,
        }

    def list_requesters(
        self,
        *,
        branch: str,
        date_from: str | None = None,
        date_to: str | None = None,
        cost_centers: list[str] | None = None,
        request_number: str | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        order_number: str | None = None,
    ) -> list[dict[str, Any]]:
        where_clause, params = build_purchase_request_lines_filters(
            branch=branch,
            date_from=date_from,
            date_to=date_to,
            cost_centers=cost_centers,
            request_number=request_number,
            product_code=product_code,
            supplier_code=supplier_code,
            order_number=order_number,
        )
        sql = build_purchase_request_requesters_sql(where_clause=where_clause)
        with self as repo:
            rows = repo.execute_query(sql, tuple(params))
        items: list[dict[str, Any]] = []
        seen: set[str] = set()
        for row in rows:
            user_id = str(row.get("requester_protheus_user_id") or "").strip()
            if not user_id or user_id in seen:
                continue
            seen.add(user_id)
            items.append(
                {
                    "protheus_user_id": user_id,
                    "code": (row.get("requester_code") or "").strip() or None,
                    "name": (row.get("requester_name") or "").strip() or None,
                }
            )
        return items

    def get_request_lines(
        self,
        *,
        branch: str,
        request_number: str,
        cost_centers: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        where_clause, params = build_purchase_request_lines_filters(
            branch=branch,
            date_from=date_from,
            date_to=date_to,
            cost_centers=cost_centers,
            request_number=request_number,
        )
        list_sql = build_purchase_request_lines_list_sql(
            where_clause=where_clause,
            offset=0,
            page_size=MAX_PAGE_SIZE,
        )
        with self as repo:
            rows = repo.execute_query(list_sql, tuple(params) + (0, MAX_PAGE_SIZE))
        lines = [_normalize_line_row(row) for row in rows]
        self._attach_orders_and_receipts(lines)
        return lines

    def _attach_orders_and_receipts(self, lines: list[dict[str, Any]]) -> None:
        if not lines:
            return
        keys = [
            (line["branch"], line["request_number"], line["request_item"])
            for line in lines
        ]
        orders_sql, orders_params = build_purchase_orders_for_lines_sql(keys)
        with self as repo:
            order_rows = repo.execute_query(orders_sql, tuple(orders_params))
        orders = [_normalize_order_row(row) for row in order_rows]
        order_keys = [
            (
                order["branch"],
                order["order_number"],
                order["order_item"],
                order["supplier_code"],
                order["supplier_store"],
                order["product_code"],
            )
            for order in orders
        ]
        receipts_sql, receipts_params = build_receipts_for_orders_sql(order_keys)
        with self as repo:
            receipt_rows = repo.execute_query(receipts_sql, tuple(receipts_params))
        receipts = [_normalize_receipt_row(row) for row in receipt_rows]
        receipts_by_order: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for receipt in receipts:
            key = (
                receipt["branch"],
                receipt["purchase_order_number"],
                receipt["purchase_order_item"],
            )
            receipts_by_order.setdefault(key, []).append(receipt)
        for order in orders:
            key = (order["branch"], order["order_number"], order["order_item"])
            order["receipts"] = receipts_by_order.get(key, [])
        orders_by_line: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for order in orders:
            key = (
                order["branch"],
                order["source_request_number"],
                order["source_request_item"],
            )
            orders_by_line.setdefault(key, []).append(order)
        for line in lines:
            key = (line["branch"], line["request_number"], line["request_item"])
            line["purchase_orders"] = orders_by_line.get(key, [])
