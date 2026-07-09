from app.application.dto.commercial.get_sales_order_otd_line_detail_request import (
    GetSalesOrderOtdLineDetailRequest,
)
from app.domain.ports.commercial.sales_order_otd_repository_port import (
    SalesOrderOtdRepositoryPort,
)


class GetSalesOrderOtdLineDetailUseCase:
    def __init__(self, *, sales_order_otd_repository: SalesOrderOtdRepositoryPort):
        self._sales_order_otd_repository = sales_order_otd_repository

    def execute(self, request: GetSalesOrderOtdLineDetailRequest) -> dict:
        line = self._sales_order_otd_repository.get_sales_order_otd_line_detail(request)
        if not line:
            raise ValueError("Linha de pedido de venda não encontrada.")

        return {
            "branch": request.branch,
            "order_number": request.order_number,
            "line_item": request.line_item,
            "line": line,
        }
