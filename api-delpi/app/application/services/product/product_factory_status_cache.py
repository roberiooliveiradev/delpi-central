from __future__ import annotations

from typing import Any

from app.application.dto.product.product_playbook_request import ProductPlaybookRequest
from app.composition.query_cache_composer import build_query_cache


def product_factory_status_cache_key(request: ProductPlaybookRequest, *, max_depth: int) -> str:
    return "|".join(
        [
            "product-factory-status",
            request.code,
            str(max_depth),
            request.reference_date or "",
            request.date_start or "",
            request.date_end or "",
            request.branch or "",
        ]
    )


def get_cached_product_factory_status(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_product_factory_status(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)
