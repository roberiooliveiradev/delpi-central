# app/application/use_cases/products/get_product_sales_open_orders_use_case.py
from app.domain.ports.product_sales_open_orders_repository_port import ProductSalesOpenOrdersRepositoryPort
from app.application.dto.get_product_sales_open_orders_request import GetProductSalesOpenOrdersRequest


class GetProductSalesOpenOrdersUseCase:

    def __init__(
        self,
        repository: ProductSalesOpenOrdersRepositoryPort
    ):
        self.repository = repository

    def execute(
        self,
        dto: GetProductSalesOpenOrdersRequest
    ):

        result = self.repository.get_sales_open_orders(
            code=dto.code
        )

        return result.__dict__