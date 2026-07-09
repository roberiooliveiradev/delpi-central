from __future__ import annotations

from app.application.dto.commercial.get_sales_order_otd_panel_request import (
    GetSalesOrderOtdPanelRequest,
)
from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.domain.ports.commercial.sales_order_otd_repository_port import (
    SalesOrderOtdRepositoryPort,
)


class GetSalesOrderOtdPanelUseCase:
    def __init__(self, *, sales_order_otd_repository: SalesOrderOtdRepositoryPort):
        self._sales_order_otd_repository = sales_order_otd_repository

    def execute(self, request: GetSalesOrderOtdPanelRequest) -> dict:
        summary_request = SalesOrderOtdRequest(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            customer_segment=request.customer_segment,
        )
        indicator = self._sales_order_otd_repository.get_sales_order_otd(summary_request)
        lines_page = self._sales_order_otd_repository.list_sales_order_otd_lines(request)

        total_lines = int(indicator.total_lines or 0)
        on_time_lines = int(indicator.on_time_lines or 0)
        late_lines = int(indicator.late_lines or 0)
        late_percentage = (
            round(late_lines * 100.0 / total_lines, 2) if total_lines > 0 else 0.0
        )

        return {
            "branch": request.branch or "consolidated",
            "start_date": request.start_date or "",
            "end_date": request.end_date or "",
            "customer_segment": request.customer_segment,
            "summary": {
                "total_lines": total_lines,
                "on_time_lines": on_time_lines,
                "late_lines": late_lines,
                "sales_order_otd_pct": indicator.sales_order_otd_pct,
                "late_percentage": late_percentage,
            },
            "lines": lines_page.to_dict(),
        }
