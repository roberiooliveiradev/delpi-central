"""TOTVS repository for the R03/P7 stock-inventory snapshot (SB9/SB1)."""

from __future__ import annotations

from app.domain.ports.financeiro_stock_inventory.stock_inventory_repository_port import (
    StockInventoryRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

from . import stock_inventory_sql, work_in_process_sql


class StockInventoryRepository(BaseRepository, StockInventoryRepositoryPort):
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

    def totals(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        warehouse: str | None,
    ) -> dict:
        query, params = stock_inventory_sql.build_totals_query(
            snapshot_date=snapshot_date,
            branches=branches,
            product_types=product_types,
            warehouse=warehouse,
        )
        with self:
            return self.execute_one(query, params) or {}

    def list_items(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        warehouse: str | None,
        page: int,
        page_size: int,
    ) -> list[dict]:
        query, params = stock_inventory_sql.build_items_query(
            snapshot_date=snapshot_date,
            branches=branches,
            product_types=product_types,
            warehouse=warehouse,
            page=page,
            page_size=page_size,
        )
        with self:
            return self.execute_query(query, params)

    def summary_by_type(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        warehouse: str | None,
    ) -> list[dict]:
        query, params = stock_inventory_sql.build_summary_by_type_query(
            snapshot_date=snapshot_date,
            branches=branches,
            product_types=product_types,
            warehouse=warehouse,
        )
        with self:
            return self.execute_query(query, params)

    def summary_by_warehouse(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        warehouse: str | None,
    ) -> list[dict]:
        query, params = stock_inventory_sql.build_summary_by_warehouse_query(
            snapshot_date=snapshot_date,
            branches=branches,
            product_types=product_types,
            warehouse=warehouse,
        )
        with self:
            return self.execute_query(query, params)

    def p7_totals(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        process_warehouse: str,
    ) -> dict:
        query, params = stock_inventory_sql.build_p7_totals_query(
            snapshot_date=snapshot_date,
            branches=branches,
            product_types=product_types,
            process_warehouse=process_warehouse,
        )
        with self:
            return self.execute_one(query, params) or {}

    def work_in_process_by_type(
        self,
        *,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        movement_cutoff: str,
        op_alive_cutoff: str,
    ) -> list[dict]:
        query, params = work_in_process_sql.build_work_in_process_by_type_query(
            branches=branches,
            product_types=product_types,
            movement_cutoff=movement_cutoff,
            op_alive_cutoff=op_alive_cutoff,
        )
        with self:
            return self.execute_query(query, params)

    def work_in_process_detail(
        self,
        *,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        movement_cutoff: str,
        op_alive_cutoff: str,
        page: int,
        page_size: int,
    ) -> list[dict]:
        query, params = work_in_process_sql.build_work_in_process_detail_query(
            branches=branches,
            product_types=product_types,
            movement_cutoff=movement_cutoff,
            op_alive_cutoff=op_alive_cutoff,
            page=page,
            page_size=page_size,
        )
        with self:
            return self.execute_query(query, params)

    def work_in_process_detail_count(
        self,
        *,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        movement_cutoff: str,
        op_alive_cutoff: str,
    ) -> int:
        query, params = (
            work_in_process_sql.build_work_in_process_detail_count_query(
                branches=branches,
                product_types=product_types,
                movement_cutoff=movement_cutoff,
                op_alive_cutoff=op_alive_cutoff,
            )
        )
        with self:
            row = self.execute_one(query, params) or {}
        return int(row.get("item_count") or 0)
