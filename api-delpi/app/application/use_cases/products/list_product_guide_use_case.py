# app/application/use_cases/products/list_product_guide_use_case.py
from app.domain.ports.product_guide_repository_port import ProductGuideRepositoryPort
from app.application.dto.list_product_guide_request import ListProductGuideRequest
from app.application.models.page import Page


class ListProductGuideUseCase:

    def __init__(self, repository: ProductGuideRepositoryPort):
        self.repository = repository

    def execute(self, dto: ListProductGuideRequest):

        max_depth = dto.max_depth or 999

        rows = self.repository.fetch_guide_rows(
            dto.code,
            dto.branch,
            max_depth
        )

        # modo full
        if dto.page is None or dto.page_size is None:

            return {
                "items": [
                    r.to_dict() if hasattr(r, "to_dict") else vars(r)
                    for r in rows
                ],
                "page": None,
                "page_size": None,
                "total": len(rows),
                "total_pages": None
            }

        # modo paginado
        offset = (dto.page - 1) * dto.page_size
        paginated = rows[offset: offset + dto.page_size]

        page = Page(
            items=paginated,
            total=len(rows),
            page=dto.page,
            page_size=dto.page_size
        )

        return page.to_dict()