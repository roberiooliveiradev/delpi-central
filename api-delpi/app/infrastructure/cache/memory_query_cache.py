from __future__ import annotations

from typing import Any

from app.domain.ports.query_cache_port import QueryCachePort
from app.infrastructure.cache.ttl_cache import TtlCache


class MemoryQueryCache(QueryCachePort):
    def __init__(self, *, ttl_seconds: float) -> None:
        self._cache: TtlCache[Any] = TtlCache(ttl_seconds=ttl_seconds)

    def get(self, key: str) -> Any | None:
        return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self._cache.set(key, value)

    def invalidate_all(self) -> None:
        self._cache.invalidate_all()
