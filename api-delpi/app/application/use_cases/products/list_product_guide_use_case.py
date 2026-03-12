# app/application/use_cases/products/list_product_guide_use_case.py
from app.domain.ports.product_guide_repository_port import ProductGuideRepositoryPort
from app.application.dto.list_product_guide_request import ListProductGuideRequest
from app.infrastructure.persistence.pagination import build_page_response


class ListProductGuideUseCase:

    def __init__(self, repository: ProductGuideRepositoryPort):
        self.repository = repository

    def execute(self, dto: ListProductGuideRequest):

        total, items = self.repository.list_guide(
            code=dto.code,
            page=dto.page,
            page_size=dto.page_size,
            branch=dto.branch,
            max_depth=dto.max_depth
        )

        data = [
            i.__dict__
            for i in items
        ]

        return build_page_response(
            data,
            total,
            dto.page,
            dto.page_size
        )