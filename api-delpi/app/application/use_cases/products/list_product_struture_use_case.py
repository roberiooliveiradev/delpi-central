# app/application/use_cases/products/list_product_structure_use_case.py

from app.domain.ports.product_structure_repository_port import ProductStructureRepositoryPort
from app.application.services.bom_tree_builder import BomTreeBuilder
from app.application.dto.list_product_structured_request import ListProductStructureRequest
from app.application.models.page import Page


class ListProductStructureUseCase:

    def __init__(self, repository: ProductStructureRepositoryPort):
        self._repository = repository

    def execute(self, request: ListProductStructureRequest):

        max_depth = request.max_depth or 999

        rows = self._repository.fetch_structure_rows(
            request.code,
            max_depth
        )

        root = BomTreeBuilder.build(rows, request.code)

        if not root:
            return {
                "root": None,
                "items": [],
                "page": None,
                "page_size": None,
                "total": 0,
                "total_pages": 0
            }

        # modo full
        if request.page is None or request.page_size is None:
            return {
                "root": {
                    "code": root.code,
                    "description": root.description,
                    "type": root.type,
                    "unit": root.unit,
                    "quantity": root.quantity
                },
                "items": [c.to_dict() for c in root.components],
                "page": None,
                "page_size": None,
                "total": len(root.components),
                "total_pages": None
            }

        # modo paginado
        components = root.components
        offset = (request.page - 1) * request.page_size
        paginated = components[offset: offset + request.page_size]

        page = Page(
            items=paginated,
            total=len(components),
            page=request.page,
            page_size=request.page_size
        ).to_dict()

        page["root"] = {
            "code": root.code,
            "description": root.description,
            "type": root.type,
            "unit": root.unit,
            "quantity": root.quantity
        }

        return page