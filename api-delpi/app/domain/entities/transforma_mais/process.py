# app/entities/transforma_mais_process.py
from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class Process:
    id: str
    name_process: str
    sector_name: Optional[str]
    daily_savings: Optional[float]
    payback_months: Optional[float]
    status: Optional[str]
    implementetion_date: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)
