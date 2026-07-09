from dataclasses import dataclass
from typing import Optional


@dataclass
class GetSalesOrderOtdPanelRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    customer_segment: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_dir: str = "asc"
