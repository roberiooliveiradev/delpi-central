"""TOTVS SC7010 — pedidos de compra em aberto para lançamento-notas-fiscais."""

from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_sql import (
    open_purchase_orders_sql,
)


class TotvsInvoicePostingSc7Repository(BaseRepository):
    def list_open_purchase_orders_by_supplier(
        self,
        *,
        branch_code: str,
        supplier_code: str,
        supplier_store: str,
    ) -> list[dict[str, Any]]:
        branch = str(branch_code or "").strip()
        supplier = str(supplier_code or "").strip()
        store = str(supplier_store or "").strip()
        if not (branch and supplier and store):
            return []

        sql, params = open_purchase_orders_sql(
            branch=branch,
            product_param=None,
            supplier_code_param="?",
            supplier_store_param="?",
        )
        with self as repo:
            rows = repo.execute_query(sql, list(params) + [supplier, store])
        return [self._map_row(row) for row in rows]

    @classmethod
    def _format_protheus_date(cls, value: Any) -> str | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        if len(raw) == 8 and raw.isdigit():
            return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
        return raw

    @classmethod
    def _map_row(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {
            "branch": str(row.get("branch") or "").strip(),
            "order_number": str(row.get("order_number") or "").strip(),
            "order_item": str(row.get("order_item") or "").strip(),
            "product_code": str(row.get("product_code") or "").strip(),
            "product_description": str(row.get("product_description") or "").strip(),
            "supplier_part_number": str(row.get("supplier_part_number") or "").strip(),
            "warehouse": str(row.get("warehouse") or "").strip(),
            "unit": str(row.get("unit") or "").strip(),
            "ordered_quantity": float(row.get("ordered_quantity") or 0),
            "delivered_quantity": float(row.get("delivered_quantity") or 0),
            "open_quantity": float(row.get("open_quantity") or 0),
            "pre_invoice_quantity": float(row.get("pre_invoice_quantity") or 0),
            "issue_date": cls._format_protheus_date(row.get("issue_date")),
            "expected_delivery_date": cls._format_protheus_date(
                row.get("expected_delivery_date")
            ),
            "supplier_code": str(row.get("supplier_code") or "").strip(),
            "supplier_store": str(row.get("supplier_store") or "").strip(),
            "supplier_name": str(row.get("supplier_name") or "").strip(),
            "unit_price": float(row.get("unit_price") or 0),
            "open_merchandise_value": float(row.get("open_merchandise_value") or 0),
            "open_ipi_value": float(row.get("open_ipi_value") or 0),
            "open_freight_value": float(row.get("open_freight_value") or 0),
            "open_discount_value": float(row.get("open_discount_value") or 0),
            "open_value": float(row.get("open_value") or 0),
        }
