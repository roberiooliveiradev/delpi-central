"""Shared composition helpers for billing-portfolio forecast × realized."""

from __future__ import annotations

from typing import Any, Optional

from app.application.dto.commercial.billing_portfolio_request import (
    BillingPortfolioBaseRequest,
)
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.domain.entities.commercial.weekly_portfolio import (
    BillingPortfolioContractMeta,
    BillingPortfolioValueTrio,
)
from app.domain.ports.commercial.commercial_weekly_portfolio_repository_port import (
    CommercialWeeklyPortfolioRepositoryPort,
)
from app.domain.ports.financial.financial_query_repository_port import (
    FinancialQueryRepositoryPort,
)
from app.domain.services.commercial_analysis_filter_request import (
    CommercialAnalysisFilterRequest,
)


def to_iso_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = str(value).strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


def open_only_from_quantity_basis(quantity_basis: str) -> bool:
    return quantity_basis == "open"


def filters_from_request(
    request: BillingPortfolioBaseRequest,
) -> CommercialAnalysisFilterRequest:
    return CommercialAnalysisFilterRequest(
        start_date=request.start_date,
        end_date=request.end_date,
        branch=request.branch,
        customer_segment=request.customer_segment,
        customer_codes=request.customer_codes,
        customer_names=request.customer_names,
        exclude_customer_codes=request.exclude_customer_codes,
        exclude_customer_names=request.exclude_customer_names,
        customer_centers=request.customer_centers,
    )


def contract_meta_from_request(
    request: BillingPortfolioBaseRequest,
) -> BillingPortfolioContractMeta:
    return BillingPortfolioContractMeta(
        nature=request.nature,
        quantity_basis=request.quantity_basis,
    )


def realized_value_from_rol(
    rol_payload: dict[str, Any],
    *,
    nature: str,
) -> float:
    if nature == "rol":
        return round(float(rol_payload.get("rol") or 0), 2)
    return round(float(rol_payload.get("gross_revenue") or 0), 2)


def fetch_realized_value(
    financial: FinancialQueryRepositoryPort,
    *,
    start_date: Optional[str],
    end_date: Optional[str],
    branch: Optional[str],
    request: BillingPortfolioBaseRequest,
) -> float:
    rol_payload = financial.get_rol(
        GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            customer_segment=request.customer_segment,
            customer_codes=request.customer_codes,
            customer_names=request.customer_names,
            exclude_customer_codes=request.exclude_customer_codes,
            exclude_customer_names=request.exclude_customer_names,
            customer_centers=request.customer_centers,
        )
    )
    return realized_value_from_rol(rol_payload, nature=request.nature)


def fetch_forecast_value(
    portfolio: CommercialWeeklyPortfolioRepositoryPort,
    *,
    start_date: str,
    end_date: str,
    branch: Optional[str],
    request: BillingPortfolioBaseRequest,
) -> float:
    return portfolio.sum_delivery_forecast(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        filters=filters_from_request(request),
        open_only=open_only_from_quantity_basis(request.quantity_basis),
    )


def value_trio(
    *,
    forecast_value: float,
    realized_value: float,
) -> BillingPortfolioValueTrio:
    return BillingPortfolioValueTrio.from_parts(
        forecast_value=forecast_value,
        realized_value=realized_value,
    )
