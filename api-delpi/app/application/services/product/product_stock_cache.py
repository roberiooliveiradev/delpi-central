from __future__ import annotations

from typing import Any

from app.composition.query_cache_composer import build_query_cache


def product_stock_cache_key(
    *,
    code: str,
    page: int,
    page_size: int,
    branch: str | None,
    location: str | None,
) -> str:
    return "|".join(
        [
            "product-stock",
            str(code or "").strip(),
            str(int(page)),
            str(int(page_size)),
            str(branch or "").strip(),
            str(location or "").strip(),
        ]
    )


def get_cached_product_stock(key: str) -> dict[str, Any] | None:
    cached = build_query_cache().get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_product_stock(key: str, value: dict[str, Any]) -> None:
    build_query_cache().set(key, value)
