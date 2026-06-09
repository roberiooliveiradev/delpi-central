from __future__ import annotations

from typing import Any

from app.domain.ports.query_cache_port import QueryCachePort
from app.domain.services.query_cache_stats_service import record_cache_get, record_cache_set


class StatsTrackingQueryCache(QueryCachePort):
    def __init__(self, inner: QueryCachePort) -> None:
        self._inner = inner

    def get(self, key: str) -> Any | None:
        value = self._inner.get(key)
        record_cache_get(key, hit=value is not None)
        return value

    def set(self, key: str, value: Any) -> None:
        self._inner.set(key, value)
        record_cache_set(key)

    def invalidate_all(self) -> None:
        self._inner.invalidate_all()
