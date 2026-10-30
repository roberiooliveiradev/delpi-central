"""TOTVS repository for the R06/R07 stock-kardex engine (MATR910).

Row fetch only: the UNION SQL in ``stock_kardex_sql`` reproduces the
producer's selection predicates; classification, signs and balances are
computed by the use case. ``MV_*`` params are read from SX6 at request
time — the same values the report runtime resolves via GETMV.
"""

from __future__ import annotations

from typing import Any

from app.domain.ports.financeiro_stock_kardex.stock_kardex_repository_port import (
    StockKardexRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import (
    BaseRepository,
)
from app.infrastructure.persistence.totvs.financeiro_stock_inventory.stock_inventory_sql import (
    build_snapshot_branch_counts_query,
)
from app.infrastructure.persistence.totvs.financeiro_stock_kardex import (
    stock_kardex_sql,
)

# pyodbc parameter cap and a sane read page for chunked lookups.
_IN_CHUNK = 500


class StockKardexRepository(BaseRepository, StockKardexRepositoryPort):
    def __init__(self) -> None:
        super().__init__()
        self._param_cache: dict[str, str | None] = {}

    def snapshot_branch_counts(
        self, *, snapshot_date: str, branches: tuple[str, ...]
    ) -> dict[str, int]:
        sql, params = build_snapshot_branch_counts_query(
            snapshot_date=snapshot_date, branches=branches
        )
        with self as repo:
            rows = repo.execute_query(sql, tuple(params)) or []
        return {
            row.get("branch_code"): int(row.get("row_count") or 0)
            for row in rows
        }

    def fetch_movements(
        self,
        *,
        period_start: str,
        period_end: str,
        branches: tuple[str, ...],
        warehouses: tuple[str, ...] | None,
        product_code: str | None,
        product_type: str | None,
        document_kind: str,
    ) -> list[dict[str, Any]]:
        mv_prodimp = self._sx6_param("MV_PRODIMP")
        # MV_D3ESTOR='N' (live) → the producer drops estorno rows.
        exclude_estorno = (self._sx6_param("MV_D3ESTOR") or "N") == "N"
        # MV_D3SERVI='N' (live) → the service clause applies with the
        # CQ warehouse from MV_CQ (default '98' in the producer).
        service_clause_on = (self._sx6_param("MV_D3SERVI") or "N") == "N"
        cq_warehouse = ""
        if service_clause_on:
            cq_warehouse = (self._sx6_param("MV_CQ") or "").strip() or "98"
        sql, params = stock_kardex_sql.build_movements_query(
            period_start=period_start,
            period_end=period_end,
            branches=branches,
            warehouses=warehouses,
            product_code=product_code,
            product_type=product_type,
            document_kind=document_kind,
            imported_product=(mv_prodimp or "").strip() or None,
            exclude_estorno=exclude_estorno,
            cq_warehouse=cq_warehouse,
        )
        with self as repo:
            return repo.execute_query(sql, tuple(params)) or []

    def fetch_opening_balances(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_codes: tuple[str, ...],
        warehouses: tuple[str, ...] | None,
    ) -> dict[tuple[str, str, str], dict[str, Any]]:
        if not product_codes:
            return {}
        balances: dict[tuple[str, str, str], dict[str, Any]] = {}
        with self as repo:
            for chunk in _chunks(product_codes):
                sql, params = stock_kardex_sql.build_opening_balance_query(
                    snapshot_date=snapshot_date,
                    branches=branches,
                    product_codes=chunk,
                    warehouses=warehouses,
                )
                for row in repo.execute_query(sql, tuple(params)) or []:
                    key = (
                        row.get("branch_code") or "",
                        row.get("warehouse") or "",
                        row.get("product_code") or "",
                    )
                    balances[key] = row
        return balances

    def fetch_cost_history(
        self,
        *,
        source_table: str,
        boundary: str,
        recnos: tuple[int, ...],
    ) -> dict[int, str]:
        """Earliest ``TTAT_COLD`` per recno logged at or after
        ``boundary`` (exclusive competence end = first day after).

        The cost field is float in the movement table but the log stores
        the literal value — returned raw for the use case to cast.
        """
        mapping = stock_kardex_sql.ttat_log_table(source_table)
        if mapping is None or not recnos:
            return {}
        log_table, field_name = mapping
        sql, params = stock_kardex_sql.build_ttat_history_query(
            log_table=log_table,
            field_name=field_name,
            boundary=boundary,
        )
        wanted = set(int(r) for r in recnos)
        history: dict[int, str] = {}
        with self as repo:
            # One ranked row per recno — keep only movement recnos.
            for row in repo.execute_query(sql, tuple(params)) or []:
                recno = int(row.get("TTAT_RECNO") or 0)
                if recno in wanted:
                    history[recno] = row.get("TTAT_COLD")
        return history

    def fetch_sx6_param(self, *, param_name: str) -> str | None:
        return self._sx6_param(param_name)

    def _sx6_param(self, param_name: str) -> str | None:
        if param_name in self._param_cache:
            return self._param_cache[param_name]
        sql, params = stock_kardex_sql.build_sx6_param_query(param_name)
        with self as repo:
            row = repo.execute_one(sql, tuple(params))
        value = (row or {}).get("param_value")
        value = str(value).strip() if value is not None else None
        self._param_cache[param_name] = value or None
        return self._param_cache[param_name]


def _chunks(values: tuple) -> list[tuple]:
    return [
        tuple(values[i : i + _IN_CHUNK])
        for i in range(0, len(values), _IN_CHUNK)
    ]
