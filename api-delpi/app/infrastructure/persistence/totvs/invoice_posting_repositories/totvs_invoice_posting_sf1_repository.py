"""TOTVS SF1010 — consulta em lote de NF de entrada (somente leitura)."""
from __future__ import annotations

from typing import Any, Sequence

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.invoice_posting_repositories.totvs_invoice_posting_sf1_sql import (
    build_find_active_by_fiscal_keys_sql,
)


class TotvsInvoicePostingSf1Repository(BaseRepository):
    def find_active_by_fiscal_keys(
        self,
        keys: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        sql, params = build_find_active_by_fiscal_keys_sql(keys)
        if not sql:
            return []

        with self as repo:
            rows = repo.execute_query(sql, tuple(params))

        return [_map_sf1_row(row) for row in rows]


def _map_sf1_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_code": str(row.get("branch_code") or "").strip(),
        "supplier_code": str(row.get("supplier_code") or "").strip(),
        "supplier_store": str(row.get("supplier_store") or "").strip(),
        "document_match_key": str(row.get("document_match_key") or "").strip(),
        "series": str(row.get("series") or "").strip().upper(),
        "sf1_recno": int(row["sf1_recno"]) if row.get("sf1_recno") is not None else None,
        "erp_entry_date_raw": row.get("erp_entry_date_raw"),
        "invoice_type": str(row.get("invoice_type") or "").strip().upper() or None,
        "erp_party_code": str(row.get("erp_party_code") or "").strip() or None,
        "erp_party_store": str(row.get("erp_party_store") or "").strip() or None,
    }
