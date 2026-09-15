"""Dispatch Custom GPT Actions to shared external semantic capabilities."""

from __future__ import annotations

from typing import Any

from app.application.external_capabilities.catalog_service import build_gpt_catalog
from app.application.external_capabilities.product_search_service import search_products


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
        # HTTP decorator already enforces ENGINEERING_LMP_ACCESS; avoid double-check noise.
        return search_products(
            code=code,
            description=description,
            group_code=group_code,
            page=page,
            page_size=page_size,
            enforce_authz=False,
            tool_name="gpt_search_products",
        )
