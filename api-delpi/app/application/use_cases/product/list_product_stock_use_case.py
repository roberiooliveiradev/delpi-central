# app/application/use_cases/products/list_product_stock_use_case.py

from app.domain.ports.product.product_stock_repository_port import ProductStockRepositoryPort
from app.application.dto.product.list_product_stock_request import ListProductStockRequest


class ListProductStockUseCase:

    def __init__(self, repository: ProductStockRepositoryPort):
        self.repository = repository

    def execute(self, dto: ListProductStockRequest):

        page = self.repository.list_stock(
            code=dto.code,
            page=dto.page,
            page_size=dto.page_size,
            branch=dto.branch,
            location=dto.location
        )

        return page.to_dict()