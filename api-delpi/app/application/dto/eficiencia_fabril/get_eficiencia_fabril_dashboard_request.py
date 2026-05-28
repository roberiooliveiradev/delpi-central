from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class GetEficienciaFabrilDashboardRequest:
    date_start: date
    date_end: date
    branch: Optional[str] = None
    employee: Optional[str] = None
    work_center: Optional[str] = None
    cost_center: Optional[str] = None
    status_ok_only: bool = True
    page: int = 1
    page_size: int = 50
