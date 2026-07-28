from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from app.domain.ports.query_cache_port import QueryCachePort
from app.domain.services.query_cache_stats_service import record_cache_get, record_cache_set
from app.infrastructure.cache.singleflight import Singleflight

T = TypeVar("T")


class StatsTrackingQueryCache(QueryCachePort):
    def __init__(self, inner: QueryCachePort) -> None:
        self._inner = inner
        self._singleflight: Singleflight[Any] = Singleflight()

    def get(self, key: str) -> Any | None:
        value = self._inner.get(key)
        record_cache_get(key, hit=value is not None)
        return value

    def set(self, key: str, value: Any) -> None:
        self._inner.set(key, value)
        record_cache_set(key)

    def invalidate_all(self) -> None:
        self._inner.invalidate_all()

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        cached = self.get(key)
        if cached is not None:
            return cached

        def compute() -> T:
            again = self._inner.get(key)
            if again is not None:
                record_cache_get(key, hit=True)
                return again
            value = factory()
            self.set(key, value)
            return value

        return self._singleflight.do(key, compute)
