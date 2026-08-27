"""Use case — OTD tabular por filial (01/02)."""

from __future__ import annotations

from typing import Any, Optional

from app.application.dto.commercial.get_sales_order_otd_by_branch_request import (
    GetSalesOrderOtdByBranchRequest,
)
from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.application.use_cases.commercial.commercial_analysis_payload_helpers import (
    branch_breakdown_rows,
)
from app.infrastructure.persistence.totvs.commercial_repositories.sales_order_otd_repository import (
    SalesOrderOtdRepository,
)

FILIAL_01 = "01"
FILIAL_02 = "02"


def _to_iso_date(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    raw = str(value).strip()
    if len(raw) == 8 and raw.isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return raw


class GetSalesOrderOtdByBranchUseCase:
    def __init__(self, *, sales_order_otd_repository: SalesOrderOtdRepository) -> None:
        self._repository = sales_order_otd_repository

    def execute(self, request: GetSalesOrderOtdByBranchRequest) -> dict[str, Any]:
        start_iso = _to_iso_date(request.start_date)
        end_iso = _to_iso_date(request.end_date)
        metrics_01 = self._repository.get_sales_order_otd_analysis_summary(
            SalesOrderOtdRequest(
                branch=FILIAL_01,
                start_date=start_iso,
                end_date=end_iso,
                customer_segment=request.customer_segment,
                customer_codes=request.customer_codes,
                customer_names=request.customer_names,
                exclude_customer_codes=request.exclude_customer_codes,
                exclude_customer_names=request.exclude_customer_names,
            )
        )
        metrics_02 = self._repository.get_sales_order_otd_analysis_summary(
            SalesOrderOtdRequest(
                branch=FILIAL_02,
                start_date=start_iso,
                end_date=end_iso,
                customer_segment=request.customer_segment,
                customer_codes=request.customer_codes,
                customer_names=request.customer_names,
                exclude_customer_codes=request.exclude_customer_codes,
                exclude_customer_names=request.exclude_customer_names,
            )
        )
        items = branch_breakdown_rows(
            {"branch_01": metrics_01, "branch_02": metrics_02}
        )
        return {
            "start_date": start_iso or request.start_date,
            "end_date": end_iso or request.end_date,
            "items": items,
            "summary": {
                "items_count": len(items),
            },
        }
