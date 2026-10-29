from __future__ import annotations

from typing import Protocol


class StockInventoryRepositoryPort(Protocol):
    """Read-only access to the Protheus stock snapshot (SB9010) enriched
    with the product register (SB1010)."""

    def snapshot_branch_counts(
        self, *, snapshot_date: str, branches: tuple[str, ...]
    ) -> dict[str, int]:
        """Rows per branch at ``B9_DATA = snapshot_date`` — no functional
        filters, so snapshot presence is proven independently of scope."""
        ...

    def totals(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        warehouse: str | None,
    ) -> dict:
        """Filtered-universe counters: item_count, total_quantity, total_value."""
        ...

    def list_items(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        warehouse: str | None,
        page: int,
        page_size: int,
    ) -> list[dict]: ...

    def summary_by_type(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        warehouse: str | None,
    ) -> list[dict]: ...

    def summary_by_warehouse(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        warehouse: str | None,
    ) -> list[dict]: ...

    def p7_totals(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        process_warehouse: str,
    ) -> dict:
        """Official P7 split on the scope universe (no ``warehouse``
        filter): ``stock_value`` = EM ESTOQUE, ``process_physical_value``
        = SB9 rows in the process warehouse (MATR989 "sem-OP" block)."""
        ...

    def work_in_process_by_type(
        self,
        *,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        movement_cutoff: str,
        op_alive_cutoff: str,
    ) -> list[dict]:
        """MATR989 allocated WIP (RE* − DE* on OPs alive at emission),
        grouped by product type so the scope filter applies to the same
        product population."""
        ...

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
        """MATR989 com-OP detail rows (branch, product, OP) — the
        standalone R08 item universe."""
        ...

    def work_in_process_detail_count(
        self,
        *,
        branches: tuple[str, ...],
        product_types: tuple[str, ...] | None,
        movement_cutoff: str,
        op_alive_cutoff: str,
    ) -> int:
        """Total MATR989 com-OP detail rows for honest pagination."""
        ...
