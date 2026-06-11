from app.application.dto.product.exclusive_raw_material_catalog_request import (
    ExclusiveRawMaterialCatalogRequest,
)
from app.application.services.product.product_playbook_service import (
    build_exclusive_catalog_by_material_items,
    group_exclusive_catalog_by_finished_product,
    summarize_exclusive_catalog_by_finished_product,
    summarize_exclusive_catalog_by_material,
)
from app.domain.constants.product_exclusivity import (
    DEFAULT_EXCLUSIVE_CATALOG_LIMIT,
    DEFAULT_EXCLUSIVE_CATALOG_MAX_DEPTH,
    MAX_EXCLUSIVE_CATALOG_LIMIT,
)
from app.domain.ports.product.product_exclusive_raw_material_repository_port import (
    ProductExclusiveRawMaterialRepositoryPort,
)


class ListExclusiveRawMaterialsCatalogUseCase:

    def __init__(self, repository: ProductExclusiveRawMaterialRepositoryPort):
        self._repository = repository

    def execute(self, request: ExclusiveRawMaterialCatalogRequest) -> dict:
        max_depth = request.max_depth or DEFAULT_EXCLUSIVE_CATALOG_MAX_DEPTH
        limit = min(
            request.limit or DEFAULT_EXCLUSIVE_CATALOG_LIMIT,
            MAX_EXCLUSIVE_CATALOG_LIMIT,
        )
        offset = max(request.offset or 0, 0)

        filters = {
            "max_depth": max_depth,
            "include_test_products": request.include_test_products,
            "finished_product_code": request.finished_product_code,
            "raw_material_code": request.raw_material_code,
            "group_code": request.group_code,
        }

        totals = self._repository.fetch_exclusive_catalog_totals(**filters)

        if request.view == "by_finished_product":
            rows = self._repository.fetch_exclusive_catalog_by_finished_product(
                limit=limit,
                offset=offset,
                **filters,
            )
            items = group_exclusive_catalog_by_finished_product(rows)
            return {
                "view": request.view,
                "items": items,
                "summary": summarize_exclusive_catalog_by_finished_product(totals),
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "returned": len(items),
                },
            }

        rows = self._repository.fetch_exclusive_catalog_by_material(
            limit=limit,
            offset=offset,
            **filters,
        )
        return {
            "view": request.view,
            "items": build_exclusive_catalog_by_material_items(rows),
            "summary": summarize_exclusive_catalog_by_material(totals),
            "pagination": {
                "limit": limit,
                "offset": offset,
                "returned": len(rows),
            },
        }
