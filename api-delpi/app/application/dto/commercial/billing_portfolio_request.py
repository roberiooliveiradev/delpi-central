from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.domain.entities.commercial.weekly_portfolio import (
    normalize_billing_portfolio_nature,
    normalize_billing_portfolio_quantity_basis,
)
from app.domain.totvs.protheus_branches import optional_concrete_branch


@dataclass
class BillingPortfolioBaseRequest:
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    branch: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_codes: Optional[list[str]] = None
    customer_names: Optional[list[str]] = None
    exclude_customer_codes: Optional[list[str]] = None
    exclude_customer_names: Optional[list[str]] = None
    customer_centers: Optional[list[str]] = None
    nature: str = "order_gross"
    quantity_basis: str = "planned"

    def validate(self) -> None:
        if not self.start_date or not self.end_date:
            raise ValueError("start_date and end_date are required.")
        self.branch = optional_concrete_branch(self.branch)
        self.nature = normalize_billing_portfolio_nature(self.nature)
        self.quantity_basis = normalize_billing_portfolio_quantity_basis(
            self.quantity_basis
        )


@dataclass
class GetBillingPortfolioSummaryRequest(BillingPortfolioBaseRequest):
    pass


@dataclass
class GetBillingPortfolioSeriesRequest(BillingPortfolioBaseRequest):
    granularity: str = "week"

    def validate(self) -> None:
        super().validate()
        granularity = (self.granularity or "").strip().lower()
        if granularity not in {"day", "week", "month", "year"}:
            raise ValueError("granularity must be day, week, month or year.")
        self.granularity = granularity


@dataclass
class GetBillingPortfolioByCustomerRequest(BillingPortfolioBaseRequest):
    page: int = 1
    page_size: int = 50

    def validate(self) -> None:
        super().validate()
        page = int(self.page)
        page_size = int(self.page_size)
        if page < 1:
            raise ValueError("page must be >= 1.")
        if page_size < 1 or page_size > 500:
            raise ValueError("page_size must be between 1 and 500.")
        self.page = page
        self.page_size = page_size


@dataclass
class GetBillingPortfolioByBranchRequest(BillingPortfolioBaseRequest):
    pass
