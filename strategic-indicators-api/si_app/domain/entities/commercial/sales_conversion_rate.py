from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class SalesConversionRate:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    qtd_proposals: int = 0
    qtd_won: int = 0
    sales_conversion_rate_pct: Optional[float] = None

    def to_dict(self):
        return asdict(self)