"""Cache de curta duração do status HZA vivo da carga máquina.

Trocar de centro de trabalho não pode reconsultar a api-delpi para as ~mil
operações da filial: o snapshot já está no Postgres; só o enriquecimento HZA
é caro. Um TTL curto reaproveita o último mapa OP+operação → status.
"""

from __future__ import annotations

import threading
import time
from typing import Any

# Janela em que o PCP ainda vê o chão de fábrica «quase ao vivo» sem pagar o
# round-trip completo a cada clique de aba.
DEFAULT_TTL_SECONDS = 45.0

_lock = threading.Lock()
# branch → (monotonic_deadline, status_by_operation_key)
_CACHE: dict[str, tuple[float, dict[tuple[str, str], dict[str, Any]]]] = {}


def clear_live_status_cache(branch: str | None = None) -> None:
    """Invalida o cache (toda a filial ou a plataforma)."""
    with _lock:
        if branch is None:
            _CACHE.clear()
            return
        _CACHE.pop(str(branch).strip(), None)


def get_live_status_cache(
    branch: str,
) -> dict[tuple[str, str], dict[str, Any]] | None:
    key = str(branch).strip()
    if not key:
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


def put_live_status_cache(
    branch: str,
    status_by_key: dict[tuple[str, str], dict[str, Any]],
    *,
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> None:
    key = str(branch).strip()
    if not key:
        return
    deadline = time.monotonic() + max(0.0, float(ttl_seconds))
    with _lock:
        _CACHE[key] = (deadline, status_by_key)
