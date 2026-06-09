from __future__ import annotations

from typing import Any

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.composition.query_cache_composer import build_query_cache


def stock_value_cache_key(request: GetStockValueRequest) -> str:
    return "|".join(
        [
            "stock-value",
            request.branch or "",
            request.location or "",
            request.start_date or "",
            request.end_date or "",
            str(request.top_limit or 10),
            "summary" if request.summary_only else "full",
        ]
    )


def get_cached_stock_value_bundle(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_stock_value_bundle(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)
