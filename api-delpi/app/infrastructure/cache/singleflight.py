"""Singleflight — um compute por chave sob concorrência (anti-stampede de cache)."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class Singleflight(Generic[T]):
    """Garante que só um caller executa ``fn`` por ``key``; os demais aguardam o resultado."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._inflight: dict[str, tuple[threading.Event, dict[str, object]]] = {}

    def do(self, key: str, fn: Callable[[], T]) -> T:
        with self._lock:
            existing = self._inflight.get(key)
            if existing is None:
                event = threading.Event()
                box: dict[str, object] = {}
                self._inflight[key] = (event, box)
                is_leader = True
            else:
                event, box = existing
                is_leader = False

        if not is_leader:
            event.wait()
            if "error" in box:
                raise box["error"]  # type: ignore[misc]
            return box["value"]  # type: ignore[return-value]

        try:
            value = fn()
            box["value"] = value
            return value
        except Exception as exc:
            box["error"] = exc
            raise
        finally:
            event.set()
            with self._lock:
                current = self._inflight.get(key)
                if current is not None and current[0] is event:
                    del self._inflight[key]
