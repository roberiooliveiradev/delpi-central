"""Repository port for the R11 billing-exclusion roster engine."""

from __future__ import annotations

from typing import Any, Protocol


class BillingExclusionRosterRepositoryPort(Protocol):
    """Reads the SD2 billing population the roster is drawn from.

    No business rule lives here — historical-criteria classification,
    sibling evaluation and findings are resolved at the application
    layer over the returned rows.
    """

    def fetch_lines(
        self,
        *,
        period_start: str,
        period_end: str,
        branches: tuple[str, ...],
        product_group: str | None,
        product_code: str | None,
        document: str | None,
        customer_code: str | None,
        tes: str | None,
    ) -> list[dict[str, Any]]:
        """In-competence SD2 lines related to the roster criteria —
        rows where ``D2_GRUPO`` matches the roster group OR ``D2_TES``
        matches the roster TES (union of both predicates so the
        out-of-criteria population stays observable, DV-R11-04). SB1
        description, SA1 name and SF4 attributes resolved at read time;
        document sibling metrics computed without row multiplication.
        """
        ...
