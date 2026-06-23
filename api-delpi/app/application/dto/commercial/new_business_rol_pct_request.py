from dataclasses import dataclass
from typing import Optional


@dataclass
class NewBusinessRolPctRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    customer_segment: Optional[str] = None
