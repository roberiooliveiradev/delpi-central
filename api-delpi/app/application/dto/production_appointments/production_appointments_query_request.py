from __future__ import annotations

from dataclasses import dataclass

from app.domain.production.production_appointments.production_appointments_scope import (
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    SERIES_GROUP_BY_OPTIONS,
    VALID_BRANCHES,
)
from app.domain.services.production.production_appointments_list_search_service import (
    ProductionAppointmentsListSearchService,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)


@dataclass(frozen=True, slots=True)
class ProductionAppointmentsQueryRequest:
    branch: str
    date_start: str | None = None
    date_end: str | None = None
    work_center: str | None = None
    op: str | None = None
    product: str | None = None
    search: str | None = None
    group_by: str = "day"
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE

    @classmethod
    def from_query(
        cls,
        *,
        branch: str,
        date_start: str | None = None,
        date_end: str | None = None,
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
        search: str | None = None,
        group_by: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> ProductionAppointmentsQueryRequest:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError('branch inválida. Use "01" (SC) ou "02" (ES).')

        resolved_group = (group_by or "day").strip().lower()
        if resolved_group not in SERIES_GROUP_BY_OPTIONS:
            raise ValueError('group_by inválido. Use "day" ou "day_work_center".')

        resolved_page = page if page is not None else DEFAULT_PAGE
        resolved_size = page_size if page_size is not None else DEFAULT_PAGE_SIZE
        if resolved_page < 1:
            raise ValueError("page deve ser >= 1.")
        if resolved_size < 1 or resolved_size > MAX_PAGE_SIZE:
            raise ValueError(f"page_size deve estar entre 1 e {MAX_PAGE_SIZE}.")

        return cls(
            branch=normalized_branch,
            date_start=date_start.strip() if date_start else None,
            date_end=date_end.strip() if date_end else None,
            work_center=work_center.strip() if work_center else None,
            op=op.strip() if op else None,
            product=product.strip() if product else None,
            search=ProductionAppointmentsListSearchService.normalize_term(search),
            group_by=resolved_group,
            page=resolved_page,
            page_size=resolved_size,
        )

    def protheus_closed_open(self) -> tuple[str, str]:
        return ProtheusDateRangeService.resolve_closed_open_period(
            date_start=self.date_start,
            date_end=self.date_end,
        )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
