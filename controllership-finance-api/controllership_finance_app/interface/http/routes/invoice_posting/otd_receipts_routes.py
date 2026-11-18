"""GLPI #852: snapshot fiscal mínimo, exclusivo do owner LNF para OTD.

Sem permissão humana de LNF ou acesso SQL cruzado à base dos plugins.
A rota exige o token de serviço interno e não herda a superfície MCP.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from delpi_auth.service_token import request_has_valid_internal_service_token
from controllership_finance_app.infrastructure.invoice_posting.postgres_invoice_posting_repository import (
    PostgresInvoicePostingRepository,
)

router = APIRouter(tags=["Integrações internas LNF"])
_MAX_ROWS = 10000

# Sem migração. A identidade fiscal segue o matching de SF1 do LNF.
_SQL = """
WITH candidates AS (
    SELECT
        branch_code,
        document_match_key,
        supplier_code,
        supplier_store,
        series,
        sf1_recno,
        (received_at AT TIME ZONE 'America/Sao_Paulo')::date AS received_date,
        erp_entry_date,
        COUNT(*) OVER (
            PARTITION BY branch_code, supplier_code, supplier_store,
                         document_match_key,
                         CASE
                           WHEN btrim(series) ~ '^[0-9]+$'
                           THEN COALESCE(NULLIF(LTRIM(btrim(series), '0'), ''), '0')
                           ELSE upper(btrim(series))
                         END
        ) AS fiscal_key_count
    FROM lancamento_notas_fiscais.invoice_posting_requests
    WHERE status = 'posted'
      AND sf1_recno IS NOT NULL
      AND sf1_recno > 0
      AND (%s::text IS NULL OR branch_code = %s)
      AND (
          (received_at AT TIME ZONE 'America/Sao_Paulo')::date BETWEEN %s AND %s
          OR erp_entry_date BETWEEN %s AND %s
      )
)
SELECT branch_code, document_match_key, supplier_code, supplier_store,
       series, sf1_recno, received_date, erp_entry_date
FROM candidates
WHERE fiscal_key_count = 1
ORDER BY branch_code, document_match_key, series, supplier_code, supplier_store
LIMIT %s
"""


def _normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "branch_code": str(row["branch_code"]).strip(),
            "document_match_key": str(row["document_match_key"]).strip(),
            "supplier_code": str(row["supplier_code"]).strip(),
            "supplier_store": str(row["supplier_store"]).strip(),
            "series": str(row["series"] or "").strip().upper(),
            "sf1_recno": int(row["sf1_recno"]),
            "received_date": row["received_date"].isoformat(),
            "erp_entry_date": row["erp_entry_date"].isoformat()
            if row["erp_entry_date"] is not None else None,
        }
        for row in rows
    ]


@router.get("/internal/otd-receipts", operation_id="get_internal_lnf_otd_receipts")
def get_internal_lnf_otd_receipts(
    request: Request,
    start_date: date = Query(...),
    end_date: date = Query(...),
    branch: str | None = Query(None),
) -> dict[str, Any]:
    if not request_has_valid_internal_service_token(request):
        raise HTTPException(status_code=403, detail="Forbidden")
    if branch not in (None, "01", "02"):
        raise HTTPException(status_code=422, detail="Filial inválida")
    if end_date < start_date or (end_date - start_date).days > 3660:
        raise HTTPException(status_code=422, detail="Período inválido")
    rows = PostgresInvoicePostingRepository().fetch_all(
        _SQL,
        (branch, branch, start_date, end_date, start_date, end_date, _MAX_ROWS + 1),
    )
    if len(rows) > _MAX_ROWS:
        # Falha fechada: nunca responder um snapshot truncado como se completo fosse.
        raise HTTPException(status_code=503, detail="Snapshot OTD excedeu limite seguro")
    return {
        "complete": True,
        "source": "lancamento_notas_fiscais",
        "items": _normalize_rows(rows),
    }
