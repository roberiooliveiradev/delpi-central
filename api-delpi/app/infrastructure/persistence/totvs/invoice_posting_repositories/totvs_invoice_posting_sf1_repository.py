"""TOTVS SF1010 — consulta em lote de NF de entrada (somente leitura)."""
from __future__ import annotations

from typing import Any, Sequence

from app.infrastructure.persistence.totvs.base_repository import BaseRepository


class TotvsInvoicePostingSf1Repository(BaseRepository):
    def find_active_by_fiscal_keys(
        self,
        keys: Sequence[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        unique: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str, str, str]] = set()
        for raw in keys:
            branch = str(raw.get("branch_code") or "").strip()
            supplier = str(raw.get("supplier_code") or "").strip()
            store = str(raw.get("supplier_store") or "").strip()
            doc_key = str(raw.get("document_match_key") or "").strip()
            series = str(raw.get("series") or "").strip().upper()
            if not (branch and supplier and store and doc_key):
                continue
            token = (branch, supplier, store, doc_key, series)
            if token in seen:
                continue
            seen.add(token)
            unique.append(
                {
                    "branch_code": branch,
                    "supplier_code": supplier,
                    "supplier_store": store,
                    "document_match_key": doc_key,
                    "series": series,
                }
            )

        if not unique:
            return []

        clauses: list[str] = []
        params: list[Any] = []
        for key in unique:
            clauses.append(
                """
                (
                    RTRIM(SF1.F1_FILIAL) = ?
                    AND RTRIM(SF1.F1_FORNECE) = ?
                    AND RTRIM(SF1.F1_LOJA) = ?
                    AND RIGHT(REPLICATE('0', 9) + RTRIM(SF1.F1_DOC), 9) = ?
                    AND UPPER(RTRIM(SF1.F1_SERIE)) = ?
                )
                """
            )
            params.extend(
                [
                    key["branch_code"],
                    key["supplier_code"],
                    key["supplier_store"],
                    key["document_match_key"],
                    key["series"],
                ]
            )

        sql = f"""
            SELECT
                RTRIM(SF1.F1_FILIAL) AS branch_code,
                RTRIM(SF1.F1_FORNECE) AS supplier_code,
                RTRIM(SF1.F1_LOJA) AS supplier_store,
                RIGHT(REPLICATE('0', 9) + RTRIM(SF1.F1_DOC), 9) AS document_match_key,
                UPPER(RTRIM(SF1.F1_SERIE)) AS series,
                SF1.R_E_C_N_O_ AS sf1_recno,
                RTRIM(SF1.F1_DTDIGIT) AS erp_entry_date_raw
            FROM SF1010 SF1 WITH (NOLOCK)
            WHERE SF1.D_E_L_E_T_ = ''
              AND RTRIM(SF1.F1_DOC) NOT LIKE '%[^0-9]%'
              AND RTRIM(SF1.F1_DOC) <> ''
              AND (
                {" OR ".join(clauses)}
              )
        """

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
    }
