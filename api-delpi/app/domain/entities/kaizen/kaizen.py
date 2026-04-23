from dataclasses import dataclass, asdict
from typing import Optional


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
    branch: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)