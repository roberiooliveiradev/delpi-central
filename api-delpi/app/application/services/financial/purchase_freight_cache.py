from __future__ import annotations

from typing import Any

from app.application.dto.financial.purchase_freight_links_request import (
    PurchaseFreightLinksRequest,
)
from app.composition.query_cache_composer import build_query_cache

CACHE_NAMESPACE = "purchase-freight-links"


def purchase_freight_links_cache_key(
    request: PurchaseFreightLinksRequest,
    *,
    limit: int,
) -> str:
    return "|".join(
        [
            CACHE_NAMESPACE,
            request.branch or "",
            request.issue_start or "",
            request.issue_end or "",
            request.entry_start or "",
            request.entry_end or "",
            request.supplier or "",
            request.invoice_document or "",
            request.freight_document or "",
            str(limit),
        ]
    )


def get_cached_purchase_freight_links(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_purchase_freight_links(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)
