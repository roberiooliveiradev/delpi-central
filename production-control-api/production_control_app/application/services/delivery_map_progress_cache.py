"""Cache curto do progresso vivo do mapa de entrega por filial + conjuntos."""

from __future__ import annotations

import threading
import time
from typing import Any

DEFAULT_TTL_SECONDS = 15.0

_lock = threading.Lock()
# (branch, conjuntos_fingerprint) → (deadline, payload)
_CACHE: dict[tuple[str, str], tuple[float, dict[str, Any]]] = {}


def get_delivery_map_progress_cache(
    branch: str,
    conjuntos_fingerprint: str,
) -> dict[str, Any] | None:
    key = (str(branch).strip(), str(conjuntos_fingerprint).strip())
    if not key[0] or not key[1]:
        return None
    now = time.monotonic()
    with _lock:
        hit = _CACHE.get(key)
        if hit is None:
            return None
        deadline, payload = hit
        if now >= deadline:
            _CACHE.pop(key, None)
            return None
        return payload


def put_delivery_map_progress_cache(
    branch: str,
    conjuntos_fingerprint: str,
    payload: dict[str, Any],
    *,
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> None:
    key = (str(branch).strip(), str(conjuntos_fingerprint).strip())
    if not key[0] or not key[1]:
        return
    deadline = time.monotonic() + max(0.0, float(ttl_seconds))
    with _lock:
        _CACHE[key] = (deadline, payload)
