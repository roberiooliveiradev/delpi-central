"""Repository — incremental SC7 rows linked to an SC (poller)."""

from __future__ import annotations

from typing import Any

from app.application.services.product.protheus_field_normalizer import protheus_date_to_iso
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories.purchase_request_linked_orders_sql import (
    build_recent_linked_orders_max_recno_sql,
    build_recent_linked_orders_sql,
    clamp_linked_orders_limit,
    normalize_after_recno,
)


def _normalize_linked_order_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "recno": int(row.get("recno") or 0),
        "branch": (row.get("branch") or "").strip(),
        "order_number": (row.get("order_number") or "").strip(),
        "order_item": (row.get("order_item") or "").strip(),
        "request_number": (row.get("request_number") or "").strip(),
        "request_item": (row.get("request_item") or "").strip(),
        "product_code": (row.get("product_code") or "").strip(),
        "product_description": (row.get("product_description") or "").strip() or None,
        "supplier_code": (row.get("supplier_code") or "").strip() or None,
        "supplier_name": (row.get("supplier_name") or "").strip() or None,
        "expected_delivery_date": protheus_date_to_iso(row.get("expected_delivery_date")),
        "requester_protheus_user_id": (
            (row.get("requester_protheus_user_id") or "").strip() or None
        ),
    }


class PurchaseRequestLinkedOrdersRepository(BaseRepository):
    def list_recent_linked_orders(
        self,
        *,
        after_recno: int | None = 0,
        limit: int | None = None,
    ) -> dict[str, Any]:
        safe_after = normalize_after_recno(after_recno)
        safe_limit = clamp_linked_orders_limit(limit)
        list_sql = build_recent_linked_orders_sql(limit=safe_limit)
        max_sql = build_recent_linked_orders_max_recno_sql()
        with self as repo:
            rows = repo.execute_query(list_sql, (safe_after,))
            max_row = repo.execute_one(max_sql)
        items = [_normalize_linked_order_row(row) for row in rows]
        max_recno = int((max_row or {}).get("max_recno") or 0)
        if items:
            max_recno = max(max_recno, max(int(item["recno"]) for item in items))
        return {
            "items": items,
            "after_recno": safe_after,
            "limit": safe_limit,
            "max_recno": max_recno,
        }
