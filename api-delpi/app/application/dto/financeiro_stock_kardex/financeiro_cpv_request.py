"""Typed request for the dedicated R06 CPV contract (doc 122 §6, D-O1).

Same competence conventions as the kardex request; the CPV window is
the full month on ``D2_EMISSAO``. Branch remains a data filter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.totvs.protheus_branches import (
    BRANCH_SCOPE_ALL,
    PROTHEUS_BRANCH_CODES,
    normalize_branch_scope,
)

from .stock_kardex_request import StockKardexQueryRequest

_PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(frozen=True, slots=True)
class FinanceiroCpvRequest:
    period: str
    branch: str = BRANCH_SCOPE_ALL
    top_limit: int = 10

    @classmethod
    def from_query(
        cls,
        *,
        period: str | None,
        branch: str | None = None,
        top_limit: int = 10,
    ) -> "FinanceiroCpvRequest":
        normalized_period = str(period or "").strip()
        if not _PERIOD_PATTERN.match(normalized_period):
            raise ValueError("period inválido. Use o formato YYYY-MM.")
        request = cls(
            period=normalized_period,
            branch=normalize_branch_scope(branch),
            top_limit=max(1, min(int(top_limit or 10), 50)),
        )
        StockKardexQueryRequest.from_query(period=request.period)
        return request

    def period_start(self) -> str:
        year, month = (int(part) for part in self.period.split("-"))
        return f"{year:04d}-{month:02d}-01"

    def period_end(self) -> str:
        import calendar

        year, month = (int(part) for part in self.period.split("-"))
        last_day = calendar.monthrange(year, month)[1]
        return f"{year:04d}-{month:02d}-{last_day:02d}"

    def period_end_compact(self) -> str:
        return self.period_end().replace("-", "")

    def requested_branches(self) -> tuple[str, ...]:
        if self.branch == BRANCH_SCOPE_ALL:
            return PROTHEUS_BRANCH_CODES
        return (self.branch,)
