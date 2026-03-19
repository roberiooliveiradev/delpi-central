# app/application/dto/kaizen/kaizen_summary_request.py
from dataclasses import dataclass
from typing import Optional


@dataclass
class KaizenSummaryRequest:
    title: Optional[str] = None
    status: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None