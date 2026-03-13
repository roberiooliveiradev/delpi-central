# app/application/use_cases/products/list_product_internal_movements_use_case.py

from app.domain.ports.product.product_internal_movements_repository_port import ProductInternalMovementsRepositoryPort
from app.application.dto.product.list_product_internal_movements_request import ListProductInternalMovementsRequest


class ListProductInternalMovementsUseCase:

    def __init__(self, repository: ProductInternalMovementsRepositoryPort):
        self.repository = repository

    def execute(self, dto: ListProductInternalMovementsRequest):

        page = self.repository.list_internal_movements(
            code=dto.code,
            page=dto.page,
            page_size=dto.page_size,
            date_start=dto.date_start,
            date_end=dto.date_end,
            branch=dto.branch,
            location=dto.location,
            tm=dto.tm,
            op=dto.op
        )

        return page.to_dict()