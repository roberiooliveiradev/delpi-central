# app/application/use_cases/products/list_product_inspection_use_case.py
from app.domain.ports.product_inspection_repository_port import ProductInspectionRepositoryPort
from app.application.dto.list_product_inspection_request import ListProductInspectionRequest
from app.application.models.page import Page


class ListProductInspectionUseCase:

    def __init__(self, repository: ProductInspectionRepositoryPort):
        self.repository = repository

    def execute(self, dto: ListProductInspectionRequest):

        # FULL MODE → sem limite de profundidade
        max_depth = dto.max_depth or 999

        inspections = self.repository.fetch_inspection_rows(
            code=dto.code,
            max_depth=max_depth
        )

        data = [
            {
                "product_code": i.product_code,
                "bom_level": i.bom_level,
                "has_inspection": i.has_inspection,
                "header": i.header,
                "measurable_tests": i.measurable_tests,
                "textual_tests": i.textual_tests,
            }
            for i in inspections
        ]

        # -------------------------
        # FULL MODE
        # -------------------------

        if dto.page is None or dto.page_size is None:

            return {
                "items": data,
                "page": None,
                "page_size": None,
                "total": len(data),
                "total_pages": None
            }

        # -------------------------
        # PAGINATED MODE
        # -------------------------

        offset = (dto.page - 1) * dto.page_size
        paginated = data[offset: offset + dto.page_size]

        page = Page(
            items=paginated,
            total=len(data),
            page=dto.page,
            page_size=dto.page_size
        ).to_dict()

        return page