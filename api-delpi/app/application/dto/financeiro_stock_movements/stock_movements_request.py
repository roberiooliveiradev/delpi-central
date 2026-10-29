"""Typed request for the R05 stock-movements summary (MATR320 rule).

Contract decisions (doc 85 §5 BR-R05-001/003):
- ``period`` is a competence ``YYYY-MM``; the movement window is the
  full calendar month and the closing balance is read at the last
  calendar day — never silently substituted by another month;
- ``branch`` is a data filter only (PO decision: no per-branch access
  segregation); ``all`` consolidates every known Protheus branch;
- ``report_scope`` selects the operational view (all products or
  MP/PI/PA) — same B1_TIPO selection as the sibling P7 engine.
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass

from app.domain.totvs.protheus_branches import (
    BRANCH_SCOPE_ALL,
    PROTHEUS_BRANCH_CODES,
    normalize_branch_scope,
)

from app.application.dto.financeiro_stock_inventory.constantes import (
    MP_PI_PA_PRODUCT_TYPES,
    REPORT_SCOPE_ALL_PRODUCTS,
    REPORT_SCOPES,
)

_PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True, slots=True)
class StockMovementsQueryRequest:
    period: str
    branch: str = BRANCH_SCOPE_ALL
    report_scope: str = REPORT_SCOPE_ALL_PRODUCTS

    @classmethod
    def from_query(
        cls,
        *,
        period: str | None,
        branch: str | None = None,
        report_scope: str | None = None,
    ) -> "StockMovementsQueryRequest":
        normalized_period = str(period or "").strip()
        if not _PERIOD_PATTERN.match(normalized_period):
            raise ValueError("period inválido. Use o formato YYYY-MM.")

        normalized_branch = normalize_branch_scope(branch)

        resolved_scope = (report_scope or REPORT_SCOPE_ALL_PRODUCTS).strip()
        if resolved_scope not in REPORT_SCOPES:
            raise ValueError(
                "report_scope inválido. Valores aceitos: "
                + ", ".join(sorted(REPORT_SCOPES))
            )

        request = cls(
            period=normalized_period,
            branch=normalized_branch,
            report_scope=resolved_scope,
        )
        request.reference_date()
        return request

    def reference_date(self) -> str:
        """YYYYMMDD of the last calendar day of the competence."""
        year, month = (int(part) for part in self.period.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}{month:02d}{last_day:02d}"

    def reference_date_iso(self) -> str:
        ref = self.reference_date()
        return f"{ref[0:4]}-{ref[4:6]}-{ref[6:8]}"

    def period_start(self) -> str:
        """YYYYMMDD of the first day of the competence."""
        year, month = (int(part) for part in self.period.split("-"))
        return f"{year:04d}{month:02d}01"

    def period_start_iso(self) -> str:
        start = self.period_start()
        return f"{start[0:4]}-{start[4:6]}-{start[6:8]}"

    def requested_branches(self) -> tuple[str, ...]:
        """Concrete branch codes the query must cover (data filter only)."""
        if self.branch == BRANCH_SCOPE_ALL:
            return PROTHEUS_BRANCH_CODES
        return (self.branch,)

    def product_types(self) -> tuple[str, ...] | None:
        """B1_TIPO restriction for the mp_pi_pa view; ``None`` = all types."""
        if self.report_scope == REPORT_SCOPE_ALL_PRODUCTS:
            return None
        return MP_PI_PA_PRODUCT_TYPES
