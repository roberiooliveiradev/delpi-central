# app/application/use_cases/products/get_product_sales_open_orders_use_case.py
from app.application.dto.product.get_product_sales_open_orders_request import (
    GetProductSalesOpenOrdersRequest,
)
from app.domain.ports.product.product_sales_open_orders_repository_port import (
    ProductSalesOpenOrdersRepositoryPort,
)


class GetProductSalesOpenOrdersUseCase:

    def __init__(
        self,
        repository: ProductSalesOpenOrdersRepositoryPort,
    ):
        self.repository = repository

    def execute(
        self,
        dto: GetProductSalesOpenOrdersRequest,
        *,
        scope,
    ):
        allowed_customers = None
        if not scope.unrestricted:
            allowed_customers = scope.allowed_customers or frozenset()
        result = self.repository.get_sales_open_orders(
            code=dto.code,
            branch=dto.branch,
            page=dto.page,
            page_size=dto.page_size,
            allowed_customers=allowed_customers,
        )
        return result.as_payload()
