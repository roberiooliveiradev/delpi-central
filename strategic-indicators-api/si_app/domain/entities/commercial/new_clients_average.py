from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class NewClientsAverage:
    branch: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    first_date: Optional[str] = None
    last_date: Optional[str] = None
    total_new_clients: int = 0
    qtd_months: int = 0
    monthly_average: Optional[float] = None

    def to_dict(self):
        return asdict(self)