"""Repositório — linhas SD2/SF2 por cliente+loja+filial e lote de produtos."""

from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_outbound_invoice_line_items_sql import (
    CHUNK_SIZE,
    chunk_codes,
    line_items_sql,
)
from app.infrastructure.persistence.totvs.pedidos_venda_abertos.customer_outbound_invoices_repository import (
    _iso_date,
    _trim,
    map_situation,
)


class CustomerOutboundInvoiceLineItemsRepository(BaseRepository):
    def list_line_items(
        self,
        *,
        branch: str,
        customer_code: str,
        customer_store: str,
        issue_date_start: str,
        issue_date_end: str,
        product_codes: list[str],
        exclude_returns: bool = True,
        chunk_size: int = CHUNK_SIZE,
    ) -> list[dict[str, Any]]:
        codes = sorted({_trim(code) for code in product_codes if _trim(code)})
        if not codes:
            return []
        branch_n = _trim(branch)
        customer_n = _trim(customer_code)
        store_n = _trim(customer_store)
        start = _trim(issue_date_start).replace("-", "")[:8]
        end = _trim(issue_date_end).replace("-", "")[:8]
        found: list[dict[str, Any]] = []
        with self as repo:
            for chunk in chunk_codes(codes, chunk_size):
                sql = line_items_sql(
                    product_count=len(chunk), exclude_returns=exclude_returns
                )
                params = (branch_n, customer_n, store_n, start, end, *chunk)
                rows = repo.execute_query(sql, params)
                for row in rows:
                    doc_type = _trim(row.get("doc_type"))
                    found.append(
                        {
                            "branch": _trim(row.get("branch")),
                            "invoice_number": _trim(row.get("invoice_number")),
                            "invoice_series": _trim(row.get("invoice_series")),
                            "item": _trim(row.get("item")),
                            "product_code": _trim(row.get("product_code")),
                            "product_description": _trim(row.get("product_description")),
                            "unit": _trim(row.get("unit")),
                            "invoice_unit": _trim(row.get("invoice_unit")),
                            "catalog_unit": _trim(row.get("catalog_unit")),
                            "quantity": _trim(row.get("quantity")) or "0",
                            "issue_date": _iso_date(row.get("issue_date_raw")),
                            "customer_code": _trim(row.get("customer_code")),
                            "customer_store": _trim(row.get("customer_store")),
                            "doc_type": doc_type,
                            "situation": map_situation(doc_type),
                            "is_return": doc_type.upper() == "D",
                        }
                    )
        return found
