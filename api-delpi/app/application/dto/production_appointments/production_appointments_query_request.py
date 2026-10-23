from __future__ import annotations

from dataclasses import dataclass

from app.domain.production.production_appointments.production_appointments_scope import (
    BY_OP_SORTABLE_COLUMNS,
    DEFAULT_BY_OP_SORT_BY,
    DEFAULT_BY_OP_SORT_DIRECTION,
    DEFAULT_LIST_SORT_BY,
    DEFAULT_LIST_SORT_DIRECTION,
    DEFAULT_PAGE,
    DEFAULT_PAGE_SIZE,
    LIST_SORTABLE_COLUMNS,
    MAX_PAGE_SIZE,
    SERIES_GRANULARITY_OPTIONS,
    SERIES_GROUP_BY_OPTIONS,
    SORT_DIRECTIONS,
    VALID_BRANCHES,
)
from app.domain.services.production.production_appointments_list_search_service import (
    ProductionAppointmentsListSearchService,
)
from app.domain.services.production.protheus_date_range_service import (
    ProtheusDateRangeService,
)
from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass(frozen=True, slots=True)
class ProductionAppointmentsQueryRequest:
    branch: str | None
    date_start: str | None = None
    date_end: str | None = None
    work_center: str | None = None
    op: str | None = None
    product: str | None = None
    search: str | None = None
    mother_op: bool = False
    group_by: str = "day"
    granularity: str = "day"
    page: int = DEFAULT_PAGE
    page_size: int = DEFAULT_PAGE_SIZE
    sort_by: str = DEFAULT_LIST_SORT_BY
    sort_direction: str = DEFAULT_LIST_SORT_DIRECTION

    @classmethod
    def from_query(
        cls,
        *,
        branch: str | None,
        date_start: str | None = None,
        date_end: str | None = None,
        work_center: str | None = None,
        op: str | None = None,
        product: str | None = None,
        search: str | None = None,
        mother_op: bool = False,
        group_by: str | None = None,
        granularity: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        sort_by: str | None = None,
        sort_direction: str | None = None,
        sort_catalog: str = "list",
        require_branch: bool = True,
    ) -> ProductionAppointmentsQueryRequest:
        normalized_branch = optional_concrete_branch(branch)
        if normalized_branch is None:
            if require_branch:
                raise ValueError("branch é obrigatória.")
        elif normalized_branch not in VALID_BRANCHES:
            raise ValueError('branch inválida. Use "all", "01" (SC) ou "02" (ES).')

        resolved_group = (group_by or "day").strip().lower()
        if resolved_group not in SERIES_GROUP_BY_OPTIONS:
            raise ValueError('group_by inválido. Use "day" ou "day_work_center".')

        resolved_granularity = (granularity or "day").strip().lower()
        if resolved_granularity not in SERIES_GRANULARITY_OPTIONS:
            raise ValueError('granularity inválida. Use "day" ou "month".')

        resolved_page = page if page is not None else DEFAULT_PAGE
        resolved_size = page_size if page_size is not None else DEFAULT_PAGE_SIZE
        if resolved_page < 1:
            raise ValueError("page deve ser >= 1.")
        if resolved_size < 1 or resolved_size > MAX_PAGE_SIZE:
            raise ValueError(f"page_size deve estar entre 1 e {MAX_PAGE_SIZE}.")

        catalog = (sort_catalog or "list").strip().lower()
        if catalog == "by_op":
            allowed = BY_OP_SORTABLE_COLUMNS
            default_sort = DEFAULT_BY_OP_SORT_BY
            default_direction = DEFAULT_BY_OP_SORT_DIRECTION
        else:
            allowed = LIST_SORTABLE_COLUMNS
            default_sort = DEFAULT_LIST_SORT_BY
            default_direction = DEFAULT_LIST_SORT_DIRECTION

        resolved_sort = (sort_by or default_sort).strip()
        if resolved_sort not in allowed:
            raise ValueError(
                f"sort_by inválido. Use um de: {', '.join(sorted(allowed))}."
            )
        resolved_direction = (sort_direction or default_direction).strip().lower()
        if resolved_direction not in SORT_DIRECTIONS:
            raise ValueError('sort_direction inválida. Use "asc" ou "desc".')

        return cls(
            branch=normalized_branch,
            date_start=date_start.strip() if date_start else None,
            date_end=date_end.strip() if date_end else None,
            work_center=work_center.strip() if work_center else None,
            op=op.strip() if op else None,
            product=product.strip() if product else None,
            search=ProductionAppointmentsListSearchService.normalize_term(search),
            mother_op=bool(mother_op),
            group_by=resolved_group,
            granularity=resolved_granularity,
            page=resolved_page,
            page_size=resolved_size,
            sort_by=resolved_sort,
            sort_direction=resolved_direction,
        )

    def protheus_closed_open(self) -> tuple[str, str]:
        return ProtheusDateRangeService.resolve_closed_open_period(
            date_start=self.date_start,
            date_end=self.date_end,
        )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size
