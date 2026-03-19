# app/domain/entities/kaizen/kaizen.py
from dataclasses import dataclass, field, asdict
from typing import Optional, List


@dataclass
class Kaizen:
    id: str
    title: str
    date_implemented: Optional[str]
    status: Optional[str]
    accountable: Optional[str]
    sector: Optional[str]
    investment: Optional[float]
    daily_savings: Optional[float]

    def to_dict(self)->dict:
        return asdict(self)