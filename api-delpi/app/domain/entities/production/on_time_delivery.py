from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class OnTimeDelivery:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_ops_finished: Optional[int] = None
    on_time_ops: Optional[int] = None
    late_ops: Optional[int] = None
    on_time_delivery_pct: Optional[float] = None

    def to_dict(self):
        return asdict(self)