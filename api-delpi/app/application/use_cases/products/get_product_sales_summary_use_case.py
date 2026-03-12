# app/application/use_cases/products/get_product_sales_summary_use_case.py
from app.domain.ports.product_sales_repository_port import ProductSalesRepositoryPort
from app.application.dto.get_product_sales_summary_request import GetProductSalesSummaryRequest


class GetProductSalesSummaryUseCase:

    def __init__(
        self,
        repository: ProductSalesRepositoryPort
    ):
        self.repository = repository

    def execute(
        self,
        dto: GetProductSalesSummaryRequest
    ):

        summary = self.repository.get_sales_summary(
            code=dto.code
        )

        return summary.__dict__