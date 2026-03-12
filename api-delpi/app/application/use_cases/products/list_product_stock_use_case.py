# app/application/use_cases/products/list_product_stock_use_case.py
from app.domain.ports.product_stock_repository_port import ProductStockRepositoryPort
from app.application.dto.list_product_stock_request import ListProductStockRequest
from app.infrastructure.persistence.pagination import build_page_response


class ListProductStockUseCase:

    def __init__(self, repository: ProductStockRepositoryPort):
        self.repository = repository

    def execute(self, dto: ListProductStockRequest):

        total, items = self.repository.list_stock(
            code=dto.code,
            page=dto.page,
            page_size=dto.page_size,
            branch=dto.branch,
            location=dto.location
        )

        data = [i.__dict__ for i in items]

        return build_page_response(
            data,
            total,
            dto.page,
            dto.page_size
        )