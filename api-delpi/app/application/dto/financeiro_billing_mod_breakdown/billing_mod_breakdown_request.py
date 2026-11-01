"""Typed request for the R09 billing × MOD breakdown (doc 141, DR-1/DR-2).

Contract decisions:
- ``period`` is a competence ``YYYY-MM``; the window is the full calendar
  month over the ``D2_EMISSAO`` axis (same as the DLP204 ``MV_PAR01/02``);
- ``branch`` is a data filter only (PO decision, doc 49 §8) — ``all``
  covers both Protheus branches, mirroring the artifact's per-branch tabs.
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

_PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True, slots=True)
class BillingModBreakdownRequest:
    period: str
    branch: str = BRANCH_SCOPE_ALL

    @classmethod
    def from_query(
        cls, *, period: str | None, branch: str | None = None
    ) -> "BillingModBreakdownRequest":
        normalized_period = str(period or "").strip()
        if not _PERIOD_PATTERN.match(normalized_period):
            raise ValueError("period inválido. Use o formato YYYY-MM.")
        return cls(
            period=normalized_period,
            branch=normalize_branch_scope(branch),
        )

    def period_start(self) -> str:
        """YYYYMMDD of the first calendar day of the competence."""
        year, month = (int(part) for part in self.period.split("-"))
        return f"{year:04d}{month:02d}01"

    def period_end(self) -> str:
        """YYYYMMDD of the last calendar day of the competence."""
        year, month = (int(part) for part in self.period.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}{month:02d}{last_day:02d}"

    def requested_branches(self) -> tuple[str, ...]:
        if self.branch == BRANCH_SCOPE_ALL:
            return PROTHEUS_BRANCH_CODES
        return (self.branch,)
