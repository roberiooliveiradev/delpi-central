from dataclasses import dataclass
from typing import Optional


@dataclass
class GetInventoryTurnoverRequest:
    branch: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    strict_idd_period: bool = False