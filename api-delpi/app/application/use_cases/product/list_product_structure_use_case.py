# app/application/use_cases/products/list_product_structure_use_case.py

from app.domain.ports.product.product_structure_repository_port import ProductStructureRepositoryPort
from app.domain.services.product.product_bom_validity_filter_service import (
    ProductBomValidityFilterService,
)
from app.application.services.bom_tree_builder import BomTreeBuilder
from app.application.dto.product.list_product_structured_request import ListProductStructureRequest
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

        bom_validity = ProductBomValidityFilterService.response_metadata()

        if not root:
            # Full-mode empty: omit null pagination placeholders. Emitting
            # page/page_size/total_pages=null made MCP completeness UNKNOWN
            # (is_complete=false) even when the empty set was authoritative.
            return {
                "root": None,
                "items": [],
                "total": 0,
                "bom_validity": bom_validity,
            }

        # modo full — entire direct-component set for the requested depth;
        # do not emit null page/page_size/total_pages (those classify as
        # pagination UNKNOWN and falsely mark the BOM incomplete).
        if request.page is None or request.page_size is None:
            items = [c.to_dict() for c in root.components]
            return {
                "root": {
                    "code": root.code,
                    "description": root.description,
                    "type": root.type,
                    "unit": root.unit,
                    "quantity": root.quantity
                },
                "items": items,
                "total": len(items),
                "bom_validity": bom_validity,
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
        page["bom_validity"] = bom_validity

        return page