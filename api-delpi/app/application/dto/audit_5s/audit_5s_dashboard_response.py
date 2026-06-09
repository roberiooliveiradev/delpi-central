from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Audit5sDashboardSummary:
    audit_count: int = 0
    average_score_pct: float | None = None
    nc_total: int = 0
    nc_open: int = 0
    nc_closed: int = 0
    nc_overdue: int = 0
    filtered_senso_order: int | None = None
    filtered_senso_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Audit5sDashboardCharts:
    score_by_period: list[dict[str, Any]] = field(default_factory=list)
    score_by_area: list[dict[str, Any]] = field(default_factory=list)
    score_by_senso: list[dict[str, Any]] = field(default_factory=list)
    nc_by_status: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Audit5sDashboardItem:
    id: str
    audit_code: str
    audit_date: str
    area_name: str
    shift: str
    status: str
    overall_score_pct: float | None
    nc_total: int
    nc_open: int
    senso_score_pct: float | None = None
    auditor_names: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Audit5sDashboardPagination:
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    def to_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total": self.total,
            "total_pages": self.total_pages,
        }


@dataclass
class Audit5sDashboardResponse:
    summary: Audit5sDashboardSummary
    charts: Audit5sDashboardCharts
    items: list[Audit5sDashboardItem]
    pagination: Audit5sDashboardPagination

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "charts": self.charts.to_dict(),
            "items": [item.to_dict() for item in self.items],
            "pagination": self.pagination.to_dict(),
        }
