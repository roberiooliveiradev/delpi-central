"""Request — série de quantidade de OPs finalizadas (C2_DATRF)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.production.production_appointments.production_appointments_scope import (
    FINISHED_OPS_GRANULARITY_OPTIONS,
    VALID_BRANCHES,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)


@dataclass(frozen=True, slots=True)
class FinishedOpsSeriesQueryRequest:
    branch: str
    date_start: str | None = None
    date_end: str | None = None
    product: str | None = None
    mother_op: bool = False
    granularity: str = "day"

    @classmethod
    def from_query(
        cls,
        *,
        branch: str,
        date_start: str | None = None,
        date_end: str | None = None,
        product: str | None = None,
        mother_op: bool = False,
        granularity: str | None = None,
    ) -> FinishedOpsSeriesQueryRequest:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError('branch inválida. Use "01" (SC) ou "02" (ES).')

        resolved_granularity = (granularity or "day").strip().lower()
        if resolved_granularity not in FINISHED_OPS_GRANULARITY_OPTIONS:
            raise ValueError('granularity inválida. Use "day" ou "month".')

        return cls(
            branch=normalized_branch,
            date_start=date_start.strip() if date_start else None,
            date_end=date_end.strip() if date_end else None,
            product=product.strip() if product else None,
            mother_op=bool(mother_op),
            granularity=resolved_granularity,
        )

    def protheus_closed_open(self) -> tuple[str, str]:
        return ProtheusDateRangeService.resolve_closed_open_period(
            date_start=self.date_start,
            date_end=self.date_end,
        )
