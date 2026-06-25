from __future__ import annotations

from typing import Any

from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.composition.query_cache_composer import build_query_cache
from app.application.services.supplies.stock_value_method_service import normalize_stock_method


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
            normalize_stock_method(request.stock_method),
        ]
    )


def stock_value_breakdown_cache_key(
    request: GetStockValueRequest,
    *,
    full_kardex: bool,
    routing_only: bool = False,
) -> str:
    return "|".join(
        [
            "stock-value-breakdown",
            request.branch or "",
            request.location or "",
            request.start_date or "",
            request.end_date or "",
            "kardex" if full_kardex else "sb9",
            "routing" if routing_only else "values",
        ]
    )


def get_cached_stock_value_bundle(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_stock_value_bundle(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)


def get_cached_stock_value_breakdown(key: str) -> list[dict[str, Any]] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, list):
        return cached
    return None


def set_cached_stock_value_breakdown(key: str, value: list[dict[str, Any]]) -> None:
    build_query_cache().set(key, value)
