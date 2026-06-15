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
    annual_savings: Optional[float]
    branch: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class KaizenDetail:
    id: str
    title: str
    date_implemented: Optional[str]
    status: Optional[str]
    accountable: Optional[str]
    sector: Optional[str]
    investment: Optional[float]
    daily_savings: Optional[float]
    annual_savings: Optional[float]
    branch: Optional[str] = None
    seconds_per_occurrence: Optional[float] = None
    occurrences_per_day: Optional[float] = None
    hourly_cost: Optional[float] = None
    hours_saved_per_day: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)