from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ListAudit5sNcBoardRequest:
    branch_code: str
    date_start: date
    date_end: date
    area_id: str | None = None
    shift: str | None = None
    status: str | None = None
    priority: str | None = None
    responsible: str | None = None
    overdue_only: bool = False
    senso_order: int | None = None
    search: str | None = None
    page: int = 1
    page_size: int = 20
    sort: str = "due_date_asc"
