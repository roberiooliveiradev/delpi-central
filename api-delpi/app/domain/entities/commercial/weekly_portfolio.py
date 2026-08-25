from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True, slots=True)
class WeeklyPortfolioCustomerForecast:
    customer_code: str
    customer_name: str
    branch: str
    forecast_value: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_code": self.customer_code,
            "customer_name": self.customer_name,
            "branch": self.branch,
            "forecast_value": self.forecast_value,
        }


@dataclass(frozen=True, slots=True)
class WeeklyPortfolioBranchTotals:
    branch: str
    forecast_value: float
    realized_value: float
    variance_value: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "branch": self.branch,
            "forecast_value": self.forecast_value,
            "realized_value": self.realized_value,
            "variance_value": self.variance_value,
        }


@dataclass(frozen=True, slots=True)
class WeeklyPortfolioSnapshot:
    previous_week_by_branch: tuple[WeeklyPortfolioBranchTotals, ...]
    current_week_forecast: tuple[WeeklyPortfolioCustomerForecast, ...]

    def to_dict(self) -> dict[str, Any]:
        previous = {
            "by_branch": [item.to_dict() for item in self.previous_week_by_branch],
            "forecast_value": round(
                sum(item.forecast_value for item in self.previous_week_by_branch), 2
            ),
            "realized_value": round(
                sum(item.realized_value for item in self.previous_week_by_branch), 2
            ),
            "variance_value": round(
                sum(item.variance_value for item in self.previous_week_by_branch), 2
            ),
        }
        return {
            "previous_week": previous,
            "current_week_forecast": [
                item.to_dict() for item in self.current_week_forecast
            ],
        }
