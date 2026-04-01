from dataclasses import dataclass
from typing import Optional


@dataclass
class SalesConversionRateRequest:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None