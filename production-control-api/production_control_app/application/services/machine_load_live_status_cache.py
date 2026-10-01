"""Cache de curta duração do status HZA vivo da carga máquina.

Trocar de centro de trabalho não pode reconsultar a api-delpi para as ~mil
operações da filial: o snapshot já está no Postgres; só o enriquecimento HZA
é caro. Um TTL curto reaproveita o último mapa OP+operação → status.

A chave carrega o escopo da consulta: filial inteira (leituras gerenciais) ou
um centro de trabalho (cockpit público, que enriquece só o CT selecionado).
Sem o escopo, um mapa parcial de CT seria confundido com o mapa completo da
filial e o CT seguinte receberia status incompleto.
"""

from __future__ import annotations

import threading
import time
from typing import Any

# Janela em que o PCP ainda vê o chão de fábrica «quase ao vivo» sem pagar o
# round-trip completo a cada clique de aba.
DEFAULT_TTL_SECONDS = 45.0

_lock = threading.Lock()
# (branch, scope) → (monotonic_deadline, status_by_operation_key)
_CACHE: dict[tuple[str, str], tuple[float, dict[tuple[str, str], dict[str, Any]]]] = {}


def _cache_key(branch: str, scope: str | None = None) -> tuple[str, str]:
    return (str(branch).strip(), str(scope or "").strip())


def clear_live_status_cache(
    branch: str | None = None,
    *,
    scope: str | None = None,
) -> None:
    """Invalida o cache (plataforma, filial inteira ou um escopo dela)."""
    with _lock:
        if branch is None:
            _CACHE.clear()
            return
        wanted = str(branch).strip()
        if scope is not None:
            _CACHE.pop((wanted, str(scope).strip()), None)
            return
        for key in [key for key in _CACHE if key[0] == wanted]:
            _CACHE.pop(key, None)


def get_live_status_cache(
    branch: str,
    *,
    scope: str | None = None,
) -> dict[tuple[str, str], dict[str, Any]] | None:
    key = _cache_key(branch, scope)
    if not key[0]:
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
    scope: str | None = None,
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> None:
    key = _cache_key(branch, scope)
    if not key[0]:
        return
    deadline = time.monotonic() + max(0.0, float(ttl_seconds))
    with _lock:
        _CACHE[key] = (deadline, status_by_key)
