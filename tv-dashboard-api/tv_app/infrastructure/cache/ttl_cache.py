from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


class TtlCache(Generic[T]):
    """In-process TTL cache.

    Semantic split (PERF-005):

    - ``ttl_seconds``      = freshness bound for callers that do not declare a
      consumer max-age (``max_age_seconds=None`` keeps legacy behavior).
    - ``retention_seconds`` = physical entry lifetime. Entries older than the
      default freshness bound stay stored so consumers with a larger
      acceptable age can still reuse them; no legitimate consumer may accept
      an entry older than ``retention_seconds``.
    - ``max_age_seconds`` on ``get`` = caller's maximum acceptable entry age.
      A stale-for-consumer entry is reported as a miss but NOT evicted —
      a more lenient consumer may still accept it.
    """

    def __init__(
        self,
        *,
        ttl_seconds: float,
        retention_seconds: float | None = None,
        max_entries: int = 0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._ttl_seconds = max(0.0, float(ttl_seconds))
        retention = self._ttl_seconds if retention_seconds is None else float(retention_seconds)
        self._retention_seconds = max(self._ttl_seconds, retention)
        self._max_entries = max(0, int(max_entries))
        self._clock = clock
        self._lock = threading.Lock()
        self._entries: OrderedDict[str, tuple[T, float, float]] = OrderedDict()

    @property
    def ttl_seconds(self) -> float:
        return self._ttl_seconds

    @property
    def retention_seconds(self) -> float:
        return self._retention_seconds

    def get(self, key: str, max_age_seconds: float | None = None) -> T | None:
        if self._ttl_seconds <= 0:
            return None
        bound = self._ttl_seconds if max_age_seconds is None else float(max_age_seconds)
        if bound <= 0:
            return None
        now = self._clock()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            value, stored_at, expires_at = entry
            if now >= expires_at:
                del self._entries[key]
                return None
            if now - stored_at > bound:
                # Stale for this consumer but physically alive: keep it for
                # consumers with a larger acceptable age.
                return None
            self._entries.move_to_end(key)
            return value

    def set(self, key: str, value: T) -> None:
        if self._ttl_seconds <= 0:
            return
        now = self._clock()
        with self._lock:
            self._entries.pop(key, None)
            self._entries[key] = (value, now, now + self._retention_seconds)
            while self._max_entries and len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def invalidate_all(self) -> None:
        with self._lock:
            self._entries.clear()

    def stats(self) -> dict[str, float | int]:
        with self._lock:
            stats: dict[str, float | int] = {
                "ttlSeconds": self._ttl_seconds,
                "retentionSeconds": self._retention_seconds,
                "entries": len(self._entries),
            }
            if self._max_entries:
                stats["maxEntries"] = self._max_entries
            return stats
