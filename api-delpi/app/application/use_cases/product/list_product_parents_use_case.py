# app/application/use_cases/products/list_product_parents_use_case.py

from app.domain.ports.product.product_parents_repository_port import ProductParentsRepositoryPort
from app.application.services.parents_tree_builder import ParentsTreeBuilder
from app.application.dto.product.list_product_parents_request import ListProductParentsRequest
from app.application.models.page import Page


class ListProductParentsUseCase:

    def __init__(self, repository: ProductParentsRepositoryPort):
        self._repository = repository

    def execute(self, request: ListProductParentsRequest):

        max_depth = request.max_depth or 999

        rows = self._repository.fetch_parents_rows(
            request.code,
            max_depth
        )

        root = ParentsTreeBuilder.build(rows, request.code)

        if not root:
            return {
                "root": None,
                "items": [],
                "page": None,
                "page_size": None,
                "total": 0,
                "total_pages": 0
            }

        # FULL MODE
        if request.page is None or request.page_size is None:

            return {
                "root": {
                    "code": root.code,
                    "description": root.description,
                    "type": root.type,
                    "unit": root.unit,
                    "quantity": root.quantity
                },
                "items": [p.to_dict() for p in root.parents],
                "page": None,
                "page_size": None,
                "total": len(root.parents),
                "total_pages": None
            }

        parents = root.parents

        offset = (request.page - 1) * request.page_size
        paginated = parents[offset: offset + request.page_size]

        page = Page(
            items=paginated,
            total=len(parents),
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