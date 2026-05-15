from dataclasses import dataclass
from typing import Optional


@dataclass
class GetOTDRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    top_limit: int = 5
    details_limit: int = 20