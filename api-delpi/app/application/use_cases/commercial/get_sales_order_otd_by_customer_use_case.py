"""Use case — OTD tabular por cliente."""

from __future__ import annotations

from typing import Any, Optional

from app.application.dto.commercial.get_sales_order_otd_by_customer_request import (
    GetSalesOrderOtdByCustomerRequest,
)
from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_repository import (
    SalesOrderOtdRepository,
)


def _to_iso_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = str(value).strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


class GetSalesOrderOtdByCustomerUseCase:
    def __init__(self, *, sales_order_otd_repository: SalesOrderOtdRepository) -> None:
        self._repository = sales_order_otd_repository

    def execute(self, request: GetSalesOrderOtdByCustomerRequest) -> dict[str, Any]:
        request.validate()
        start_iso = _to_iso_date(request.start_date)
        end_iso = _to_iso_date(request.end_date)
        rows = self._repository.list_sales_order_otd_analysis_by_customer(
            SalesOrderOtdRequest(
                branch=request.branch,
                start_date=start_iso,
                end_date=end_iso,
                customer_segment=request.customer_segment,
                customer_codes=request.customer_codes,
                customer_code_stores=request.customer_code_stores,
                customer_names=request.customer_names,
                exclude_customer_codes=request.exclude_customer_codes,
                exclude_customer_names=request.exclude_customer_names,
            )
        )
        total = len(rows)
        start_idx = (request.page - 1) * request.page_size
        end_idx = start_idx + request.page_size
        page_rows = rows[start_idx:end_idx]
        return {
            "start_date": start_iso or request.start_date,
            "end_date": end_iso or request.end_date,
            "branch": request.branch,
            "items": page_rows,
            "pagination": {
                "page": request.page,
                "page_size": request.page_size,
                "total": total,
                "has_more": end_idx < total,
            },
            "summary": {
                "items_count": len(page_rows),
                "customers_count": total,
            },
        }
