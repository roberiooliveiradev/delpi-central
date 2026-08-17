from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass
class PurchaseOrderOtd:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    product_type: str = "MP"
    total_lines: int = 0
    on_time_lines: int = 0
    late_lines: int = 0
    purchase_order_otd_pct: Optional[float] = None

    def to_dict(self):
        return asdict(self)
