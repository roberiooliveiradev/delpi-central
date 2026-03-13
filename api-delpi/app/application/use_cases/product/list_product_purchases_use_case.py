# app/application/use_cases/products/list_product_purchases_use_case.py
from app.domain.ports.product.product_purchases_repository_port import ProductPurchasesRepositoryPort
from app.application.dto.product.list_product_purchases_request import ListProductPurchasesRequest


class ListProductPurchasesUseCase:

    def __init__(self, repository: ProductPurchasesRepositoryPort):
        self.repository = repository

    def execute(self, dto: ListProductPurchasesRequest):

        page = self.repository.list_purchases(
            code=dto.code,
            page=dto.page,
            page_size=dto.page_size
        )

        return page.to_dict()