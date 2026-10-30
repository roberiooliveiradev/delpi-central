"""Repository port for the R06/R07 stock-kardex engine (MATR910)."""

from __future__ import annotations

from typing import Any, Protocol


class StockKardexRepositoryPort(Protocol):
    """Reads the MATR910 movement universe and its balance/cost inputs.

    No business rule lives here — classification, sign convention and
    running balances are resolved at the application layer over the
    returned rows.
    """

    def snapshot_branch_counts(
        self, *, snapshot_date: str, branches: tuple[str, ...]
    ) -> dict[str, int]:
        """Opening-snapshot row count per branch — proves SB9 presence."""
        ...

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
        """Full filtered movement union (SD1/SD2/SD3 + SB1 + SF4)."""
        ...

    def fetch_opening_balances(
        self,
        *,
        snapshot_date: str,
        branches: tuple[str, ...],
        product_codes: tuple[str, ...],
        warehouses: tuple[str, ...] | None,
    ) -> dict[tuple[str, str, str], dict[str, Any]]:
        """SB9 opening positions keyed by (branch, warehouse, product)."""
        ...

    def fetch_cost_history(
        self,
        *,
        source_table: str,
        boundary: str,
        recnos: tuple[int, ...],
    ) -> dict[int, str]:
        """As-of cost per movement recno — earliest TTAT_COLD logged
        after ``boundary`` for the table's cost field."""
        ...

    def fetch_sx6_param(self, *, param_name: str) -> str | None:
        """Protheus SX6 parameter value (filial-specific preferred)."""
        ...
