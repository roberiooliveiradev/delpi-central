# app/application/dto/transforma_mais/process_summary_response.py
from dataclasses import dataclass, asdict, field
from typing import Optional, List


@dataclass
class MonthlySummaryItem:
    month: str
    gross_savings_month: float
    gross_costs_month: float
    gross_investment_month: float
    gross_recurring_investment_month: float
    shared_resource_cost_month: float
    net_savings_month: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RangeSummary:
    start_date: Optional[str]
    end_date: Optional[str]
    accumulated_net_savings_until_now: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProcessSummaryResponse:
    implemented_solutions_count: int
    total_net_savings_until_now: float
    total_hours_saved_until_now: float
    total_gross_costs_until_now: float
    average_roi: float
    monthly_breakdown: List[MonthlySummaryItem] = field(default_factory=list)
    range_summary: Optional[RangeSummary] = None

    def to_dict(self) -> dict:
        return {
            "implemented_solutions_count": self.implemented_solutions_count,
            "total_net_savings_until_now": self.total_net_savings_until_now,
            "total_hours_saved_until_now": self.total_hours_saved_until_now,
            "total_gross_costs_until_now": self.total_gross_costs_until_now,
            "average_roi": self.average_roi,
            "monthly_breakdown": [item.to_dict() for item in self.monthly_breakdown],
            "range_summary": self.range_summary.to_dict() if self.range_summary else None,
        }