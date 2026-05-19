from __future__ import annotations

import threading
import time
from typing import Generic, TypeVar

T = TypeVar("T")


class TtlCache(Generic[T]):
    def __init__(self, *, ttl_seconds: float) -> None:
        self._ttl_seconds = max(0.0, float(ttl_seconds))
        self._lock = threading.Lock()
        self._entries: dict[str, tuple[T, float]] = {}

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

    def invalidate_all(self) -> None:
        with self._lock:
            self._entries.clear()
