from __future__ import annotations

from app.infrastructure.persistence.totvs.supplies_repositories.otd_physical_receipts import (
    physical_receipts_enabled,
)

from typing import Any

from app.application.dto.supplies.purchase_order_otd_request import PurchaseOrderOtdRequest
from app.composition.query_cache_composer import build_query_cache


def purchase_order_otd_cache_key(request: PurchaseOrderOtdRequest) -> str:
    return "|".join(
        [
            "supplies-purchase-order-otd-physical-v1"
            if physical_receipts_enabled() else "supplies-purchase-order-otd",
            request.branch or "",
            request.start_date or "",
            request.end_date or "",
        ]
    )


def get_cached_purchase_order_otd(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_purchase_order_otd(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)
