from __future__ import annotations

import copy
import threading
import time
from collections import OrderedDict
from typing import Generic, TypeVar

T = TypeVar("T")


class BoundedTtlLruCache(Generic[T]):
    """Cache local thread-safe, limitado por TTL e quantidade de entradas."""

    def __init__(self, *, ttl_seconds: float, max_entries: int) -> None:
        self._ttl_seconds = max(0.0, float(ttl_seconds))
        self._max_entries = max(0, int(max_entries))
        self._entries: OrderedDict[str, tuple[T, float]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> T | None:
        if self._ttl_seconds <= 0 or self._max_entries <= 0:
            return None
        now = time.monotonic()
        with self._lock:
            entry = self._entries.pop(key, None)
            if entry is None:
                return None
            value, expires_at = entry
            if now >= expires_at:
                return None
            self._entries[key] = (value, expires_at)
            return copy.deepcopy(value)

    def set(self, key: str, value: T) -> None:
        if self._ttl_seconds <= 0 or self._max_entries <= 0:
            return
        with self._lock:
            self._entries.pop(key, None)
            self._entries[key] = (
                copy.deepcopy(value),
                time.monotonic() + self._ttl_seconds,
            )
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def stats(self) -> dict[str, int | float]:
        with self._lock:
            return {
                "entries": len(self._entries),
                "maxEntries": self._max_entries,
                "ttlSeconds": self._ttl_seconds,
            }
