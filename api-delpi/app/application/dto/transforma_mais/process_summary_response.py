# app/application/dto/transforma_mais/process_summary_response.py
from dataclasses import dataclass, asdict, field
from typing import Optional, List


@dataclass
class MonthlySummaryItem:
    month: str
    total_savings_month: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RangeSummary:
    start_date: Optional[str]
    end_date: Optional[str]
    accumulated_savings: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProcessSummaryResponse:
    implemented_solutions: int
    total_savings_until_now: float
    total_hours_saved_until_now: float
    total_investment_until_now: float
    average_roi_percent: float
    monthly_description: List[MonthlySummaryItem] = field(default_factory=list)
    range: Optional[RangeSummary] = None

    def to_dict(self) -> dict:
        return {
            "implemented_solutions": self.implemented_solutions,
            "total_savings_until_now": self.total_savings_until_now,
            "total_hours_saved_until_now": self.total_hours_saved_until_now,
            "total_investment_until_now": self.total_investment_until_now,
            "average_roi_percent": self.average_roi_percent,
            "monthly_description": [item.to_dict() for item in self.monthly_description],
            "range": self.range.to_dict() if self.range else None,
        }