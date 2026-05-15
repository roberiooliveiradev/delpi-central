from dataclasses import dataclass
from typing import Optional


@dataclass
class Audit5SSummaryRequest:
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    branch: Optional[str] = None