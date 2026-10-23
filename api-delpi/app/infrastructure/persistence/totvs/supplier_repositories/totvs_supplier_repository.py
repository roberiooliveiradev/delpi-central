"""TOTVS SA2010 — busca e lookup de fornecedores (somente leitura)."""
from __future__ import annotations

import re
from typing import Any

from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.pagination import paginate

_PAGED_SORT_COLUMNS: dict[str, str] = {
    "supplier_name": "SA2.A2_NOME",
    "supplier_code": "SA2.A2_COD",
    "tax_id": "SA2.A2_CGC",
    "state": "SA2.A2_EST",
}
_PAGED_SORT_DEFAULT = "supplier_name"


class TotvsSupplierRepository(BaseRepository):
    def search_suppliers(self, *, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = (query or "").strip()
        if not q:
            return []

        limit = max(1, min(int(limit), 50))
        digits = re.sub(r"\D", "", q)
        params: list[Any] = []
        clauses = ["SA2.D_E_L_E_T_ = ''"]

        or_parts: list[str] = [
            "SA2.A2_COD LIKE ?",
            "SA2.A2_NOME COLLATE Latin1_General_CI_AI LIKE ?",
            "SA2.A2_NREDUZ COLLATE Latin1_General_CI_AI LIKE ?",
        ]
        params.extend([f"{q}%", f"%{q}%", f"%{q}%"])

        if digits:
            or_parts.append("SA2.A2_CGC LIKE ?")
            params.append(f"%{digits}%")

        # código + loja "000001 01" ou "000001-01"
        parts = re.split(r"[\s\-/]+", q)
        if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
            or_parts.append("(SA2.A2_COD LIKE ? AND SA2.A2_LOJA LIKE ?)")
            params.extend([f"{parts[0].strip()}%", f"{parts[1].strip()}%"])

        clauses.append("(" + " OR ".join(or_parts) + ")")
        where_sql = " AND ".join(clauses)

        sql = f"""
            SELECT TOP ({limit})
                RTRIM(SA2.A2_COD) AS supplier_code,
                RTRIM(SA2.A2_LOJA) AS supplier_store,
                RTRIM(SA2.A2_NOME) AS supplier_name,
                RTRIM(SA2.A2_NREDUZ) AS supplier_short_name,
                RTRIM(SA2.A2_CGC) AS tax_id,
                RTRIM(SA2.A2_EST) AS state,
                RTRIM(SA2.A2_MSBLQL) AS msblql
            FROM SA2010 SA2
            WHERE {where_sql}
            ORDER BY SA2.A2_NOME, SA2.A2_COD, SA2.A2_LOJA
        """

        with self as repo:
            rows = repo.execute_query(sql, tuple(params))

        return [_map_supplier_row(row) for row in rows]

    def get_supplier(
        self,
        *,
        supplier_code: str,
        supplier_store: str,
    ) -> dict[str, Any] | None:
        code = (supplier_code or "").strip()
        store = (supplier_store or "").strip()
        if not code or not store:
            return None

        sql = """
            SELECT TOP 1
                RTRIM(SA2.A2_COD) AS supplier_code,
                RTRIM(SA2.A2_LOJA) AS supplier_store,
                RTRIM(SA2.A2_NOME) AS supplier_name,
                RTRIM(SA2.A2_NREDUZ) AS supplier_short_name,
                RTRIM(SA2.A2_CGC) AS tax_id,
                RTRIM(SA2.A2_EST) AS state,
                RTRIM(SA2.A2_MSBLQL) AS msblql
            FROM SA2010 SA2
            WHERE SA2.D_E_L_E_T_ = ''
              AND RTRIM(SA2.A2_COD) = ?
              AND RTRIM(SA2.A2_LOJA) = ?
            ORDER BY SA2.R_E_C_N_O_
        """
        with self as repo:
            row = repo.execute_one(sql, (code, store))
        return _map_supplier_row(row) if row else None


    def search_suppliers_paged(
        self,
        *,
        query: str | None = None,
        state: str | None = None,
        blocked: bool | None = None,
        tax_id: str | None = None,
        sort_by: str = _PAGED_SORT_DEFAULT,
        sort_dir: str = "asc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Paged supplier search scoped to SA2010 company 01 (A2_FILIAL='').

        Same match semantics as ``search_suppliers`` (code prefix, CI_AI name
        contains, digit-only tax id contains, code+store pair) with server-side
        pagination, allowlisted sort and deterministic tiebreak. ``tax_id`` is a
        separate exact filter on digit-normalized A2_CGC (canonical duplicate
        check) — ANDed with the remaining clauses, never ORed into ``query``.
        """
        clauses = ["SA2.D_E_L_E_T_ = ''", "SA2.A2_FILIAL = ''"]
        params: list[Any] = []

        q = (query or "").strip()
        if q:
            or_parts: list[str] = [
                "SA2.A2_COD LIKE ?",
                "SA2.A2_NOME COLLATE Latin1_General_CI_AI LIKE ?",
                "SA2.A2_NREDUZ COLLATE Latin1_General_CI_AI LIKE ?",
            ]
            params.extend([f"{q}%", f"%{q}%", f"%{q}%"])

            digits = re.sub(r"\D", "", q)
            if digits:
                or_parts.append("SA2.A2_CGC LIKE ?")
                params.append(f"%{digits}%")

            parts = re.split(r"[\s\-/]+", q)
            if len(parts) >= 2 and parts[0].strip() and parts[1].strip():
                or_parts.append("(SA2.A2_COD LIKE ? AND SA2.A2_LOJA LIKE ?)")
                params.extend([f"{parts[0].strip()}%", f"{parts[1].strip()}%"])

            clauses.append("(" + " OR ".join(or_parts) + ")")

        uf = (state or "").strip().upper()
        if uf:
            clauses.append("SA2.A2_EST = ?")
            params.append(uf)

        tax_digits = re.sub(r"\D", "", tax_id or "")
        if tax_digits:
            clauses.append(
                "REPLACE(REPLACE(REPLACE("
                "SA2.A2_CGC, '.', ''), '/', ''), '-', '') = ?"
            )
            params.append(tax_digits)

        if blocked is True:
            clauses.append("SA2.A2_MSBLQL = '1'")
        elif blocked is False:
            clauses.append("ISNULL(SA2.A2_MSBLQL, '') <> '1'")

        where_sql = " AND ".join(clauses)
        paging = paginate(page, page_size, tier_id="page_20_100")

        sort_column = _PAGED_SORT_COLUMNS.get(sort_by) or _PAGED_SORT_COLUMNS[
            _PAGED_SORT_DEFAULT
        ]
        direction = "DESC" if str(sort_dir).lower() == "desc" else "ASC"

        count_sql = f"SELECT COUNT(*) AS total FROM SA2010 SA2 WHERE {where_sql}"
        sql = f"""
            SELECT
                RTRIM(SA2.A2_COD) AS supplier_code,
                RTRIM(SA2.A2_LOJA) AS supplier_store,
                RTRIM(SA2.A2_NOME) AS supplier_name,
                RTRIM(SA2.A2_NREDUZ) AS supplier_short_name,
                RTRIM(SA2.A2_CGC) AS tax_id,
                RTRIM(SA2.A2_EST) AS state,
                RTRIM(SA2.A2_MSBLQL) AS msblql
            FROM SA2010 SA2
            WHERE {where_sql}
            ORDER BY {sort_column} {direction}, SA2.A2_COD, SA2.A2_LOJA
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        with self as repo:
            total_row = repo.execute_one(count_sql, tuple(params))
            total = int(total_row["total"]) if total_row else 0
            rows = repo.execute_query(
                sql, tuple(params + [paging["offset"], paging["page_size"]])
            )

        return [_map_supplier_row(row) for row in rows], total


def _map_supplier_row(row: dict[str, Any]) -> dict[str, Any]:
    tax_id = re.sub(r"\D", "", str(row.get("tax_id") or ""))
    msblql = str(row.get("msblql") or "").strip()
    code = str(row.get("supplier_code") or "").strip()
    store = str(row.get("supplier_store") or "").strip()
    return {
        "supplier_id": f"{code}{store}" if code and store else None,
        "supplier_code": code,
        "supplier_store": store,
        "supplier_name": str(row.get("supplier_name") or "").strip(),
        "supplier_short_name": str(row.get("supplier_short_name") or "").strip() or None,
        "tax_id": tax_id or None,
        "state": str(row.get("state") or "").strip() or None,
        "blocked": msblql == "1",
    }
