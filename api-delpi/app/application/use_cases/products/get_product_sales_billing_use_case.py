# app/application/use_cases/products/get_product_sales_billing_use_case.py
from app.domain.ports.product_sales_billing_repository_port import ProductSalesBillingRepositoryPort
from app.application.dto.get_product_sales_billing_request import GetProductSalesBillingRequest


class GetProductSalesBillingUseCase:

    def __init__(
        self,
        repository: ProductSalesBillingRepositoryPort
    ):
        self.repository = repository

    def execute(
        self,
        dto: GetProductSalesBillingRequest
    ):

        result = self.repository.get_sales_billing(
            code=dto.code
        )

        return result.__dict__