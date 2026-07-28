from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Generic, TypeVar

from app.infrastructure.cache.singleflight import Singleflight

T = TypeVar("T")


class TtlCache(Generic[T]):
    def __init__(self, *, ttl_seconds: float) -> None:
        self._ttl_seconds = max(0.0, float(ttl_seconds))
        self._lock = threading.Lock()
        self._entries: dict[str, tuple[T, float]] = {}
        self._singleflight: Singleflight[T] = Singleflight()

    def get(self, key: str) -> T | None:
        if self._ttl_seconds <= 0:
            return None

        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None

            value, expires_at = entry
            if time.monotonic() >= expires_at:
                del self._entries[key]
                return None

            return value

    def set(self, key: str, value: T) -> None:
        if self._ttl_seconds <= 0:
            return

        with self._lock:
            self._entries[key] = (value, time.monotonic() + self._ttl_seconds)

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        cached = self.get(key)
        if cached is not None:
            return cached

        def compute() -> T:
            again = self.get(key)
            if again is not None:
                return again
            value = factory()
            self.set(key, value)
            return value

        return self._singleflight.do(key, compute)

    def invalidate_all(self) -> None:
        with self._lock:
            self._entries.clear()
