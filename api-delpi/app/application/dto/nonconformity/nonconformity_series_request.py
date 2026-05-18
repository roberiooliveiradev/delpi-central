from dataclasses import dataclass
from typing import Optional


@dataclass
class NonconformitySeriesRequest:
    type: str = "all"
    granularity: str = "month"
    branch: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    status: Optional[str] = None
    item_code: Optional[str] = None
    description: Optional[str] = None
