"""Repository port for the R10 cost-center-expenses engine."""

from __future__ import annotations

from typing import Any, Protocol


class CostCenterExpensesRepositoryPort(Protocol):
    """Reads the SD1 expense universe and the CTT catalog rows it needs.

    No business rule lives here — universe split, exclusion reasons and
    findings are resolved at the application layer over the returned
    rows.
    """

    def fetch_lines(
        self,
        *,
        period_start: str,
        period_end: str,
        branches: tuple[str, ...],
        cost_center: str | None,
        product_code: str | None,
        document: str | None,
        supplier_code: str | None,
        tes: str | None,
    ) -> list[dict[str, Any]]:
        """Full filtered SD1 line set (SB1 description, SA2 name, CTT
        catalog status resolved at read time)."""
        ...
