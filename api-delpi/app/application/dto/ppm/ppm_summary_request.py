# app/application/dto/ppm/ppm_summary_request.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class PpmSummaryRequest:
    type: str                   # internal | external
    branch: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    product_prefix: Optional[str] = None