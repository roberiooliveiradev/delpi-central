from __future__ import annotations

from typing import Any

from collections import defaultdict

from app.domain.ports.query_cache_port import QueryCachePort
from app.domain.services.query_cache_stats_service import cache_namespace_from_key
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

    def count_keys_by_namespace(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        with self._cache._lock:
            for key in self._cache._entries:
                counts[cache_namespace_from_key(key)] += 1
        return dict(counts)
