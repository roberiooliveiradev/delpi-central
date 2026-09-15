"""Dispatch Custom GPT Actions to existing api-delpi application use cases."""

from __future__ import annotations

from typing import Any

from app.application.dto.product.list_products_requests import ListProductsRequest
from app.application.gpt_actions.catalog_service import build_gpt_catalog
from app.application.gpt_actions.constants import GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE
from app.application.gpt_actions.product_search_projection import (
    project_product_search_page,
)
from app.composition.product_composer import build_search_products_use_case


class GptActionsDispatchService:
    def get_catalog(self) -> dict[str, Any]:
        return build_gpt_catalog()

    def search_products(
        self,
        *,
        code: str | None = None,
        description: str | None = None,
        group_code: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        safe_page = max(1, int(page or 1))
        safe_size = min(
            max(1, int(page_size or GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE)),
            GPT_PRODUCT_SEARCH_MAX_PAGE_SIZE,
        )
        dto = ListProductsRequest(
            code=code,
            description=description,
            group_code=group_code,
            customer_reference=None,
            page=safe_page,
            page_size=safe_size,
        )
        result = build_search_products_use_case().execute(dto)
        return project_product_search_page(result.to_dict())
