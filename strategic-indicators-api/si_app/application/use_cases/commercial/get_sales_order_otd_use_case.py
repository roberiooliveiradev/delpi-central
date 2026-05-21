from si_app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from si_app.domain.ports.commercial.sales_order_otd_repository_port import SalesOrderOtdRepositoryPort


class GetSalesOrderOtdUseCase:
    def __init__(self, *, sales_order_otd_repository: SalesOrderOtdRepositoryPort):
        self._sales_order_otd_repository = sales_order_otd_repository

    def execute(self, request: SalesOrderOtdRequest) -> dict:
        indicator = self._sales_order_otd_repository.get_sales_order_otd(request)

        return {
            "branch": indicator.branch,
            "start_date": indicator.start_date,
            "end_date": indicator.end_date,
            "total_lines": indicator.total_lines,
            "on_time_lines": indicator.on_time_lines,
            "late_lines": indicator.late_lines,
            "sales_order_otd_pct": indicator.sales_order_otd_pct,
        }
