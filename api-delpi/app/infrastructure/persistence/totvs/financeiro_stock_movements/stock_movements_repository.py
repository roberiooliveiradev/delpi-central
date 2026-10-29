"""TOTVS repository for the R05 stock-movements summary (MATR320).

The closing-balance (SA) and snapshot-presence reads reuse the same
``stock_inventory_sql`` builders the P7 engine consumes — one snapshot
population, two report views (no duplicated balance rule).
"""

from __future__ import annotations

from app.domain.ports.financeiro_stock_movements.stock_movements_repository_port import (
    StockMovementsRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.financeiro_stock_inventory import (
    stock_inventory_sql,
)

from . import stock_movements_sql


class StockMovementsRepository(BaseRepository, StockMovementsRepositoryPort):
    def snapshot_branch_counts(
        self, *, snapshot_date: str, branches: tuple[str, ...]
    ) -> dict[str, int]:
        query, params = stock_inventory_sql.build_snapshot_branch_counts_query(
            snapshot_date=snapshot_date, branches=branches
        )
        with self:
            rows = self.execute_query(query, params)
        return {
            str(row.get("branch_code") or "").strip(): int(
                row.get("row_count") or 0
            )
            for row in rows
        }

    def closing_balance_by_type(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
    ) -> list[dict]:
        """SA MATR320 per type — SB9 grouped universe over EVERY warehouse
        (the process warehouse included, BR-R05-002/41 errata)."""
        query, params = stock_inventory_sql.build_summary_by_type_query(
            snapshot_date=snapshot_date,
            branches=branches,
            product_types=product_types,
            warehouse=None,
        )
        with self:
            return self.execute_query(query, params)

    def sd1_by_type(
        self,
        *,
        branches: tuple[str, ...],
        period_start: str,
        period_end: str,
        product_types: tuple[str, ...] | None,
    ) -> list[dict]:
        query, params = stock_movements_sql.build_sd1_by_type_query(
            branches=branches,
            period_start=period_start,
            period_end=period_end,
            product_types=product_types,
        )
        with self:
            return self.execute_query(query, params)

    def sd2_by_type(
        self,
        *,
        branches: tuple[str, ...],
        period_start: str,
        period_end: str,
        product_types: tuple[str, ...] | None,
    ) -> list[dict]:
        query, params = stock_movements_sql.build_sd2_by_type_query(
            branches=branches,
            period_start=period_start,
            period_end=period_end,
            product_types=product_types,
        )
        with self:
            return self.execute_query(query, params)

    def sd3_by_type(
        self,
        *,
        branches: tuple[str, ...],
        period_start: str,
        period_end: str,
        product_types: tuple[str, ...] | None,
    ) -> list[dict]:
        query, params = stock_movements_sql.build_sd3_by_type_query(
            branches=branches,
            period_start=period_start,
            period_end=period_end,
            product_types=product_types,
        )
        with self:
            return self.execute_query(query, params)
