"""Cache de curta duração do desempenho público do posto.

O cockpit fica aberto em tablets no chão de fábrica com refresh automático.
Eficiência e paradas vêm do TOTVS via api-delpi e mudam em minutos, não em
segundos: um TTL curto evita que N tablets no mesmo CT multipliquem a carga.
"""

from __future__ import annotations

import threading
import time
from typing import Any

DEFAULT_TTL_SECONDS = 120.0

_lock = threading.Lock()
# (branch, work_center, days) → (monotonic_deadline, payload)
_CACHE: dict[tuple[str, str, int], tuple[float, dict[str, Any]]] = {}


def _normalized_key(branch: str, work_center: str, days: int) -> tuple[str, str, int]:
    return (str(branch).strip(), str(work_center).strip(), int(days))


def clear_work_center_performance_cache(branch: str | None = None) -> None:
    """Invalida o cache (toda a filial ou a plataforma)."""
    with _lock:
        if branch is None:
            _CACHE.clear()
            return
        wanted = str(branch).strip()
        for key in [key for key in _CACHE if key[0] == wanted]:
            _CACHE.pop(key, None)


def get_work_center_performance_cache(
    *, branch: str, work_center: str, days: int
) -> dict[str, Any] | None:
    key = _normalized_key(branch, work_center, days)
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


def put_work_center_performance_cache(
    payload: dict[str, Any],
    *,
    branch: str,
    work_center: str,
    days: int,
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> None:
    key = _normalized_key(branch, work_center, days)
    if not key[0] or not key[1]:
        return
    deadline = time.monotonic() + max(0.0, float(ttl_seconds))
    with _lock:
        _CACHE[key] = (deadline, payload)
