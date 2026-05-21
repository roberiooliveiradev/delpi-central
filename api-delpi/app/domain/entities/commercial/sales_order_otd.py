from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class SalesOrderOtd:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_lines: int = 0
    on_time_lines: int = 0
    late_lines: int = 0
    sales_order_otd_pct: Optional[float] = None

    def to_dict(self):
        return asdict(self)
