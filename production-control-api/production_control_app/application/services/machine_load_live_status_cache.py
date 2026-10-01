"""Cache granular de status vivo (HZA/SC2/SH6) da carga máquina.

Fato cacheado = status de uma operação, chaveado por
(branch, production_order, operation_code) — a mesma normalização de
_operation_key no MachineLoadService. O centro de trabalho não faz
parte da identidade: leituras de CTs diferentes reaproveitam os mesmos hits,
e misses são sempre buscados em lote na api-delpi (nunca N+1).

Cada entrada expira individualmente em ~45s; refresh de snapshot limpa a
filial inteira porque operações podem sair da programação. O cache é
process-local: em vários workers/replicas cada processo mantém o seu — isso
só reduz compartilhamento de hits, nunca a correção.
"""

from __future__ import annotations

import threading
import time
from typing import Any

# Janela em que o PCP ainda vê o chão de fábrica «quase ao vivo» sem pagar o
# round-trip completo a cada clique de aba.
DEFAULT_TTL_SECONDS = 45.0

# Guarda-chuva de memória: snapshot real ~1783 operações; ordens de grandeza
# acima disso indicariam acúmulo de snapshots antigos entre refreshes.
_MAX_ENTRIES = 50_000

_lock = threading.Lock()
# (branch, production_order, operation_code) → (monotonic_deadline, status)
_CACHE: dict[tuple[str, str, str], tuple[float, dict[str, Any]]] = {}


def _key(branch: str, production_order: str, operation_code: str) -> tuple[str, str, str]:
    return (
        str(branch).strip(),
        str(production_order).strip(),
        str(operation_code).strip(),
    )


def get_live_status_many(
    branch: str,
    operation_keys: list[tuple[str, str]] | set[tuple[str, str]],
) -> tuple[dict[tuple[str, str], dict[str, Any]], set[tuple[str, str]]]:
    """Lê o cache por operação: retorna (hits, misses).

    Entrada expirada conta como miss e é removida (limpeza preguiçosa).
    """
    hits: dict[tuple[str, str], dict[str, Any]] = {}
    misses: set[tuple[str, str]] = set()
    branch_key = str(branch).strip()
    if not branch_key:
        return hits, {(o, c) for o, c in operation_keys}
    now = time.monotonic()
    with _lock:
        for order, operation in operation_keys:
            key = (branch_key, str(order).strip(), str(operation).strip())
            hit = _CACHE.get(key)
            if hit is None:
                misses.add((key[1], key[2]))
                continue
            deadline, status = hit
            if now >= deadline:
                _CACHE.pop(key, None)
                misses.add((key[1], key[2]))
            else:
                hits[(key[1], key[2])] = status
    return hits, misses


def put_live_status_many(
    branch: str,
    status_by_key: dict[tuple[str, str], dict[str, Any]],
    *,
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> None:
    """Grava respostas válidas — nunca chamado com falha/ausência."""
    branch_key = str(branch).strip()
    if not branch_key:
        return
    deadline = time.monotonic() + max(0.0, float(ttl_seconds))
    with _lock:
        for (order, operation), status in status_by_key.items():
            _CACHE[_key(branch_key, order, operation)] = (deadline, status)
        if len(_CACHE) > _MAX_ENTRIES:
            now = time.monotonic()
            for key in [k for k, (dl, _) in _CACHE.items() if now >= dl]:
                _CACHE.pop(key, None)


def invalidate_live_status_operation(
    branch: str,
    production_order: str,
    operation_code: str,
) -> None:
    """Remove somente uma operação — para eventos comprovados na fonte TOTVS."""
    with _lock:
        _CACHE.pop(_key(branch, production_order, operation_code), None)


def clear_live_status_cache(branch: str | None = None) -> None:
    """Invalida o cache (toda a plataforma ou só a filial — refresh de snapshot)."""
    with _lock:
        if branch is None:
            _CACHE.clear()
            return
        wanted = str(branch).strip()
        for key in [key for key in _CACHE if key[0] == wanted]:
            _CACHE.pop(key, None)
