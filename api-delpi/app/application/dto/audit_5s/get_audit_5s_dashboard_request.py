from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class GetAudit5sDashboardRequest:
    branch_code: str
    date_start: date
    date_end: date
    area_id: str | None = None
    shift: str | None = None
    audit_status: str | None = None
    senso_order: int | None = None
    granularity: str = "month"
    page: int = 1
    page_size: int = 20
