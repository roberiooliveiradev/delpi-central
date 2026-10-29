"""Typed request for the R03/P7 stock-inventory snapshot query.

Contract decisions (doc 49 §4-§6, master prompt §5):
- ``period`` is a competence ``YYYY-MM``; the snapshot date is the last
  calendar day of that month — never silently substituted by another month;
- ``branch`` is a data filter only (PO decision: no per-branch access
  segregation); ``all`` consolidates every known Protheus branch;
- ``report_scope`` selects the operational view (all products or MP/PI/PA).
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.totvs.protheus_branches import (
    BRANCH_SCOPE_ALL,
    PROTHEUS_BRANCH_CODES,
    normalize_branch_scope,
)

from .constantes import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MP_PI_PA_PRODUCT_TYPES,
    REPORT_SCOPE_ALL_PRODUCTS,
    REPORT_SCOPES,
)

_PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_WAREHOUSE_PATTERN = re.compile(r"^[0-9A-Za-z]{1,10}$")


@dataclass(frozen=True, slots=True)
class StockInventoryQueryRequest:
    period: str
    branch: str = BRANCH_SCOPE_ALL
    report_scope: str = REPORT_SCOPE_ALL_PRODUCTS
    warehouse: str | None = None
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE

    @classmethod
    def from_query(
        cls,
        *,
        period: str | None,
        branch: str | None = None,
        report_scope: str | None = None,
        warehouse: str | None = None,
        page: int = DEFAULT_PAGE,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> "StockInventoryQueryRequest":
        normalized_period = str(period or "").strip()
        if not _PERIOD_PATTERN.match(normalized_period):
            raise ValueError("period inválido. Use o formato YYYY-MM.")

        # Vazio/aliases PT → all; código desconhecido → ValueError.
        normalized_branch = normalize_branch_scope(branch)

        resolved_scope = (report_scope or REPORT_SCOPE_ALL_PRODUCTS).strip()
        if resolved_scope not in REPORT_SCOPES:
            raise ValueError(
                "report_scope inválido. Valores aceitos: "
                + ", ".join(sorted(REPORT_SCOPES))
            )

        normalized_warehouse = str(warehouse or "").strip() or None
        if normalized_warehouse is not None and not _WAREHOUSE_PATTERN.match(
            normalized_warehouse
        ):
            raise ValueError("warehouse inválido. Use 1–10 caracteres alfanuméricos.")

        request = cls(
            period=normalized_period,
            branch=normalized_branch,
            report_scope=resolved_scope,
            warehouse=normalized_warehouse,
            page=max(int(page or DEFAULT_PAGE), 1),
            page_size=int(page_size or DEFAULT_PAGE_SIZE),
        )
        # Malformed input must fail before any authorization/scope gate.
        request.reference_date()
        return request

    def reference_date(self) -> str:
        """YYYYMMDD of the last calendar day of the competence (snapshot key)."""
        year, month = (int(part) for part in self.period.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}{month:02d}{last_day:02d}"

    def reference_date_iso(self) -> str:
        ref = self.reference_date()
        return f"{ref[0:4]}-{ref[4:6]}-{ref[6:8]}"

    def op_alive_cutoff(self) -> str:
        """YYYYMMDD of the emission-day convention: the day after the
        month-end snapshot. MATR989/MATR460 emit the register on the
        morning after the close — OPs whose first production posting
        lands on the emission day itself are excluded from the allocated
        WIP slice (doc 80 §41.C)."""
        ref = self.reference_date()
        day = date(int(ref[0:4]), int(ref[4:6]), int(ref[6:8])) + timedelta(
            days=1
        )
        return day.strftime("%Y%m%d")

    def op_alive_cutoff_iso(self) -> str:
        cut = self.op_alive_cutoff()
        return f"{cut[0:4]}-{cut[4:6]}-{cut[6:8]}"

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
