from __future__ import annotations

import copy
import threading
import time
from collections import OrderedDict
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class BoundedTtlLruCache(Generic[T]):
    """Cache local thread-safe, limitado por TTL e quantidade de entradas.

    Semantic split (PERF-005):

    - ``ttl_seconds``       = freshness bound for callers that do not declare a
      consumer max-age (``max_age_seconds=None`` keeps legacy behavior).
    - ``retention_seconds`` = physical entry lifetime (>= ttl_seconds). Entries
      older than the default freshness bound stay stored so consumers with a
      larger acceptable age can still reuse them.
    - ``max_age_seconds`` on ``get`` = caller's maximum acceptable entry age.
      A stale-for-consumer entry is reported as a miss but NOT evicted —
      a more lenient consumer may still accept it.

    Boundary contract (inclusive on both layers): an entry is live while
    ``age <= retention_seconds`` and fresh for a consumer while
    ``age <= max_age_seconds`` — i.e. usable while
    ``age <= min(max_age, retention)``.
    """

    def __init__(
        self,
        *,
        ttl_seconds: float,
        max_entries: int,
        retention_seconds: float | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl_seconds = max(0.0, float(ttl_seconds))
        self._max_entries = max(0, int(max_entries))
        retention = self._ttl_seconds if retention_seconds is None else float(retention_seconds)
        self._retention_seconds = max(self._ttl_seconds, retention)
        self._clock = clock
        self._entries: OrderedDict[str, tuple[T, float, float]] = OrderedDict()
        self._lock = threading.Lock()
        # Decision counters — cumulative per instance lifetime; `stats()` only.
        self._hits = 0
        self._misses_absent = 0
        self._misses_expired = 0
        self._misses_stale = 0
        self._evictions_lru = 0

    def get(self, key: str, max_age_seconds: float | None = None) -> T | None:
        if self._ttl_seconds <= 0 or self._max_entries <= 0:
            return None
        bound = self._ttl_seconds if max_age_seconds is None else float(max_age_seconds)
        if bound <= 0:
            return None
        now = self._clock()
        with self._lock:
            entry = self._entries.pop(key, None)
            if entry is None:
                self._misses_absent += 1
                return None
            value, stored_at, expires_at = entry
            if now > expires_at:
                self._misses_expired += 1
                return None
            self._entries[key] = entry
            if now - stored_at > bound:
                # Stale for this consumer but physically alive: keep it for
                # consumers with a larger acceptable age.
                self._misses_stale += 1
                return None
            self._hits += 1
            return copy.deepcopy(value)

    def set(self, key: str, value: T) -> None:
        if self._ttl_seconds <= 0 or self._max_entries <= 0:
            return
        now = self._clock()
        with self._lock:
            self._entries.pop(key, None)
            self._entries[key] = (
                copy.deepcopy(value),
                now,
                now + self._retention_seconds,
            )
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
                self._evictions_lru += 1

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def stats(self) -> dict[str, int | float]:
        with self._lock:
            return {
                "entries": len(self._entries),
                "maxEntries": self._max_entries,
                "ttlSeconds": self._ttl_seconds,
                "retentionSeconds": self._retention_seconds,
                "hits": self._hits,
                "missesAbsent": self._misses_absent,
                "missesExpired": self._misses_expired,
                "missesStale": self._misses_stale,
                "evictionsLru": self._evictions_lru,
            }
