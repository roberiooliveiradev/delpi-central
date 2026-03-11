# app/application/use_cases/products/list_product_parents_use_case.py
from app.domain.ports.product_parents_repository_port import ProductParentsRepositoryPort
from app.application.services.parents_tree_builder import ParentsTreeBuilder
from app.application.dto.list_product_parents_request import ListProductParentsRequest
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
                "structure": None,
                "pagination": None
            }

        # FULL MODE

        if not request.page or not request.page_size:

            return {
                "structure": root.to_dict(),
                "pagination": None
            }

        parents = root.parents

        offset = (request.page - 1) * request.page_size
        paginated = parents[offset: offset + request.page_size]

        page = Page(
            items=paginated,
            total=len(parents),
            page=request.page,
            page_size=request.page_size
        )

        return {
            "structure": root.to_dict(),
            "pagination": page
        }