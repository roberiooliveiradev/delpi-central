# app/application/use_cases/sale/list_sale_order_use_case.py
from app.application.models.page import Page
from app.domain.entities.sale.sale_order import SaleOrder
from app.application.dto.sale_order.list_sale_order_request import ListSaleOrderRequest
from app.domain.ports.sale.sale_order_query_repository_port import SaleOrderQueryRepositoryPort


class ListSaleOrderUseCase:

    def __init__(
        self,
        repository: SaleOrderQueryRepositoryPort
    ):
        self._repository = repository

    def execute(
        self,
        request: ListSaleOrderRequest
    ) -> Page[SaleOrder]:

        return self._repository.list_sales_orders(request)