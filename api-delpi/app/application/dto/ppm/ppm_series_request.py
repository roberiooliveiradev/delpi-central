from dataclasses import dataclass
from typing import Optional


@dataclass
class PpmSeriesRequest:
    type: str
    granularity: str
    branch: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    product_prefix: Optional[str] = None
