"""Repository port for the R05 stock-movements summary (MATR320)."""

from __future__ import annotations

from typing import Protocol


class StockMovementsRepositoryPort(Protocol):
    def snapshot_branch_counts(
        self, *, snapshot_date: str, branches: tuple[str, ...]
    ) -> dict[str, int]: ...

    def closing_balance_by_type(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
    ) -> list[dict]: ...

    def sd1_by_type(
        self,
        *,
        branches: tuple[str, ...],
        period_start: str,
        period_end: str,
        product_types: tuple[str, ...] | None,
    ) -> list[dict]: ...

    def sd2_by_type(
        self,
        *,
        branches: tuple[str, ...],
        period_start: str,
        period_end: str,
        product_types: tuple[str, ...] | None,
    ) -> list[dict]: ...

    def sd3_by_type(
        self,
        *,
        branches: tuple[str, ...],
        period_start: str,
        period_end: str,
        product_types: tuple[str, ...] | None,
    ) -> list[dict]: ...
