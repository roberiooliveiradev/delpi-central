from app.application.dto.commercial.get_sales_order_otd_panel_request import (
    GetSalesOrderOtdPanelRequest,
)
from app.application.use_cases.commercial.get_sales_order_otd_panel_use_case import (
    GetSalesOrderOtdPanelUseCase,
)
from app.domain.entities.commercial.sales_order_otd import SalesOrderOtd
from app.application.models.page import Page


class FakeSalesOrderOtdRepository:
    def get_sales_order_otd(self, request):
        return SalesOrderOtd(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            total_lines=10,
            on_time_lines=8,
            late_lines=2,
            sales_order_otd_pct=80.0,
        )

    def list_sales_order_otd_lines(self, request):
        return Page(
            items=[
                {
                    "branch": "02",
                    "order_number": "000001",
                    "line_item": "01",
                    "status": "on_time",
                }
            ],
            total=1,
            page=request.page,
            page_size=request.page_size,
        )

    def get_sales_order_otd_line_detail(self, request):
        return None


def test_get_sales_order_otd_panel_use_case_returns_summary_and_lines() -> None:
    use_case = GetSalesOrderOtdPanelUseCase(
        sales_order_otd_repository=FakeSalesOrderOtdRepository()
    )

    result = use_case.execute(
        GetSalesOrderOtdPanelRequest(
            branch="02",
            start_date="2026-07-01",
            end_date="2026-07-08",
        )
    )

    assert result["summary"]["total_lines"] == 10
    assert result["summary"]["on_time_lines"] == 8
    assert result["summary"]["late_lines"] == 2
    assert result["lines"]["total"] == 1
    assert result["lines"]["items"][0]["order_number"] == "000001"
