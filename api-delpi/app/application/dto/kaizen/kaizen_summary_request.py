from dataclasses import dataclass
from typing import Optional


@dataclass
class KaizenSummaryRequest:
    title: Optional[str] = None
    status: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    branch: Optional[str] = None