from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

ALLOWED_BILLING_PORTFOLIO_NATURES = frozenset({"order_gross", "rol"})
ALLOWED_BILLING_PORTFOLIO_QUANTITY_BASES = frozenset({"planned", "open"})

FORECAST_DATE_BASIS = "C6_ENTREG"
REALIZED_DATE_BASIS = "D2_EMISSAO"
AS_OF_LIVE = "live"


def variance_value(*, forecast_value: float, realized_value: float) -> float:
    return round(float(realized_value) - float(forecast_value), 2)


def normalize_billing_portfolio_nature(value: Optional[str]) -> str:
    raw = (value or "order_gross").strip().lower()
    if raw not in ALLOWED_BILLING_PORTFOLIO_NATURES:
        raise ValueError("nature must be order_gross or rol.")
    return raw


def normalize_billing_portfolio_quantity_basis(value: Optional[str]) -> str:
    raw = (value or "planned").strip().lower()
    if raw not in ALLOWED_BILLING_PORTFOLIO_QUANTITY_BASES:
        raise ValueError("quantity_basis must be planned or open.")
    return raw


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
class WeeklyPortfolioBranchForecast:
    branch: str
    forecast_value: float

    def to_dict(self) -> dict[str, Any]:
        return {
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
    """Report-shaped Excel snapshot — not an HTTP body for billing-portfolio routes."""

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


@dataclass(frozen=True, slots=True)
class BillingPortfolioValueTrio:
    forecast_value: float
    realized_value: float
    variance_value: float

    @classmethod
    def from_parts(
        cls, *, forecast_value: float, realized_value: float
    ) -> BillingPortfolioValueTrio:
        forecast = round(float(forecast_value), 2)
        realized = round(float(realized_value), 2)
        return cls(
            forecast_value=forecast,
            realized_value=realized,
            variance_value=variance_value(
                forecast_value=forecast, realized_value=realized
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "forecast_value": self.forecast_value,
            "realized_value": self.realized_value,
            "variance_value": self.variance_value,
        }


@dataclass(frozen=True, slots=True)
class BillingPortfolioContractMeta:
    nature: str
    quantity_basis: str
    forecast_date_basis: str = FORECAST_DATE_BASIS
    realized_date_basis: str = REALIZED_DATE_BASIS
    as_of: str = AS_OF_LIVE

    def to_dict(self) -> dict[str, Any]:
        return {
            "nature": self.nature,
            "quantity_basis": self.quantity_basis,
            "forecast_date_basis": self.forecast_date_basis,
            "realized_date_basis": self.realized_date_basis,
            "as_of": self.as_of,
        }


@dataclass(frozen=True, slots=True)
class BillingPortfolioCustomerItem:
    customer_code: str
    customer_name: str
    branch: Optional[str]
    forecast_value: float
    realized_value: float
    variance_value: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_code": self.customer_code,
            "customer_name": self.customer_name,
            "branch": self.branch,
            "forecast_value": self.forecast_value,
            "realized_value": self.realized_value,
            "variance_value": self.variance_value,
        }


@dataclass(frozen=True, slots=True)
class BillingPortfolioSeriesPoint:
    periodo: str
    sort_key: str
    start_date: str
    end_date: str
    forecast_value: float
    realized_value: float
    variance_value: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "periodo": self.periodo,
            "sort_key": self.sort_key,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "forecast_value": self.forecast_value,
            "realized_value": self.realized_value,
            "variance_value": self.variance_value,
        }
