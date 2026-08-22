from __future__ import annotations

import time
from threading import Lock
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_LOCK = Lock()
_STORE: dict[str, tuple[float, Any]] = {}


def clear_cache() -> None:
    with _LOCK:
        _STORE.clear()


def cached_fetch(
    key: str,
    ttl_seconds: int,
    loader: Callable[[], T],
    *,
    refresh: bool = False,
) -> T:
    """Cache in-process por chave. `refresh=True` ignora o valor guardado."""
    now = time.monotonic()
    if not refresh and ttl_seconds > 0:
        with _LOCK:
            hit = _STORE.get(key)
        if hit is not None:
            expires_at, value = hit
            if expires_at > now:
                return value

    value = loader()
    if ttl_seconds > 0:
        with _LOCK:
            _STORE[key] = (now + ttl_seconds, value)
    return value
