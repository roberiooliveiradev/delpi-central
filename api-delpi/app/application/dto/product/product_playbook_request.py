from dataclasses import dataclass
from typing import Optional


@dataclass
class ProductPlaybookRequest:
    code: str
    max_depth: Optional[int] = None
    reference_date: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None
