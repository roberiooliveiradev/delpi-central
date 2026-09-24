"""Use case — billing portfolio by customer (forecast × realized)."""

from __future__ import annotations

from typing import Any

from app.application.dto.commercial.billing_portfolio_request import (
    GetBillingPortfolioByCustomerRequest,
)
from app.application.dto.commercial.get_rol_by_customer_request import (
    GetRolByCustomerRequest,
)
from app.application.services.pagination_envelope_builder import PaginationEnvelopeBuilder
from app.application.use_cases.commercial.billing_portfolio_helpers import (
    contract_meta_from_request,
    filters_from_request,
    open_only_from_quantity_basis,
    realized_value_from_rol,
    to_iso_date,
    value_trio,
)
from app.domain.entities.commercial.weekly_portfolio import BillingPortfolioCustomerItem
from app.domain.ports.commercial.commercial_rol_by_customer_repository_port import (
    CommercialRolByCustomerRepositoryPort,
)
from app.domain.ports.commercial.commercial_weekly_portfolio_repository_port import (
    CommercialWeeklyPortfolioRepositoryPort,
)


class GetBillingPortfolioByCustomerUseCase:
    def __init__(
        self,
        *,
        portfolio_repository: CommercialWeeklyPortfolioRepositoryPort,
        rol_by_customer_repository: CommercialRolByCustomerRepositoryPort,
    ) -> None:
        self._portfolio = portfolio_repository
        self._rol_by_customer = rol_by_customer_repository

    def execute(self, request: GetBillingPortfolioByCustomerRequest) -> dict[str, Any]:
        request.validate()
        start_iso = to_iso_date(request.start_date)
        end_iso = to_iso_date(request.end_date)
        assert start_iso and end_iso

        forecast_rows = self._portfolio.list_delivery_week_forecast_by_customer(
            start_date=start_iso,
            end_date=end_iso,
            branch=request.branch,
            filters=filters_from_request(request),
            open_only=open_only_from_quantity_basis(request.quantity_basis),
        )
        forecast_by_customer: dict[str, dict[str, Any]] = {}
        for row in forecast_rows:
            code = row.customer_code
            current = forecast_by_customer.get(code)
            if current is None:
                forecast_by_customer[code] = {
                    "customer_code": code,
                    "customer_name": row.customer_name,
                    "branch": row.branch if request.branch else None,
                    "forecast_value": row.forecast_value,
                }
            else:
                current["forecast_value"] = round(
                    float(current["forecast_value"]) + float(row.forecast_value), 2
                )
                if request.branch is None:
                    current["branch"] = None

        realized_result = self._rol_by_customer.get_rol_by_customer(
            GetRolByCustomerRequest(
                branch=request.branch,
                start_date=start_iso,
                end_date=end_iso,
                customer_segment=request.customer_segment,
                customer_codes=request.customer_codes,
                customer_names=request.customer_names,
                exclude_customer_codes=request.exclude_customer_codes,
                exclude_customer_names=request.exclude_customer_names,
                customer_centers=request.customer_centers,
                limit=500,
                include_others=False,
            )
        )
        realized_by_customer: dict[str, dict[str, Any]] = {}
        for item in realized_result.items:
            code = item.customer_code
            realized = realized_value_from_rol(
                {"rol": item.rol, "gross_revenue": item.gross_revenue},
                nature=request.nature,
            )
            current = realized_by_customer.get(code)
            if current is None:
                realized_by_customer[code] = {
                    "customer_code": code,
                    "customer_name": item.customer_name,
                    "realized_value": realized,
                }
            else:
                current["realized_value"] = round(
                    float(current["realized_value"]) + float(realized), 2
                )

        merged: list[BillingPortfolioCustomerItem] = []
        all_codes = sorted(
            set(forecast_by_customer) | set(realized_by_customer),
        )
        for code in all_codes:
            forecast_row = forecast_by_customer.get(code) or {}
            realized_row = realized_by_customer.get(code) or {}
            forecast_value = float(forecast_row.get("forecast_value") or 0)
            realized_value = float(realized_row.get("realized_value") or 0)
            if forecast_value == 0 and realized_value == 0:
                continue
            trio = value_trio(
                forecast_value=forecast_value,
                realized_value=realized_value,
            )
            merged.append(
                BillingPortfolioCustomerItem(
                    customer_code=code,
                    customer_name=str(
                        forecast_row.get("customer_name")
                        or realized_row.get("customer_name")
                        or code
                    ),
                    branch=forecast_row.get("branch")
                    if request.branch
                    else None,
                    forecast_value=trio.forecast_value,
                    realized_value=trio.realized_value,
                    variance_value=trio.variance_value,
                )
            )

        merged.sort(
            key=lambda item: (
                -abs(item.variance_value),
                -item.forecast_value,
                item.customer_code,
            )
        )
        total = len(merged)
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        page_items = merged[start_idx:end_idx]

        total_forecast = round(sum(item.forecast_value for item in merged), 2)
        total_realized = round(sum(item.realized_value for item in merged), 2)
        summary_trio = value_trio(
            forecast_value=total_forecast,
            realized_value=total_realized,
        )

        return {
            "branch": request.branch,
            "start_date": start_iso,
            "end_date": end_iso,
            **contract_meta_from_request(request).to_dict(),
            "items": [item.to_dict() for item in page_items],
            "pagination": PaginationEnvelopeBuilder.build(
                shape="paged_count",
                page=request.page,
                page_size=request.page_size,
                total=total,
                extra={"has_more": end_idx < total},
            ),
            "summary": {
                "items_count": len(page_items),
                "customers_count": total,
                **summary_trio.to_dict(),
            },
        }
