from dataclasses import dataclass
from typing import Optional


@dataclass
class GetLmpHistoryRequest:
    sale_number: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None
    revision: Optional[str] = None
