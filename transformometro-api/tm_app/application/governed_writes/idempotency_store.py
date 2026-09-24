"""In-process idempotency cache for commit_now (single-replica ACCEPT_WITH_RESIDUAL)."""

from __future__ import annotations

import threading
import time
from typing import Any

_DEFAULT_TTL_SEC = 3600
_lock = threading.Lock()
_store: dict[str, tuple[float, dict[str, Any]]] = {}


def _key(actor_id: str, idempotency_key: str) -> str:
    return f"{actor_id}::{idempotency_key}"


def get_cached(actor_id: str, idempotency_key: str) -> dict[str, Any] | None:
    k = _key(actor_id, idempotency_key)
    now = time.time()
    with _lock:
        row = _store.get(k)
        if not row:
            return None
        expires_at, payload = row
        if expires_at < now:
            _store.pop(k, None)
            return None
        return dict(payload)


def put_cached(
    actor_id: str,
    idempotency_key: str,
    payload: dict[str, Any],
    *,
    ttl_sec: int = _DEFAULT_TTL_SEC,
) -> None:
    k = _key(actor_id, idempotency_key)
    with _lock:
        _store[k] = (time.time() + ttl_sec, dict(payload))


def clear_idempotency_store() -> None:
    with _lock:
        _store.clear()
