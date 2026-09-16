from __future__ import annotations

from typing import Any

from app.domain.ports.query_cache_port import QueryCachePort


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


def get_cached_product_stock(cache: QueryCachePort, key: str) -> dict[str, Any] | None:
    cached = cache.get(key)
    if isinstance(cached, dict):
        return cached
    return None


def set_cached_product_stock(
    cache: QueryCachePort, key: str, value: dict[str, Any]
) -> None:
    cache.set(key, value)
