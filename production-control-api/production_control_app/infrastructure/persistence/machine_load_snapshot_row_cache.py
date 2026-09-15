"""Cache do snapshot da carga máquina por versão da tupla no Postgres.

A fila da filial passa de 1,8 MB de JSONB e o psycopg já entrega `payload_json`
desserializado: o custo está em **buscar** a linha (~52 ms medidos), não em
decodificá-la depois. Como o snapshot só muda em ações explícitas do PCP, vale
perguntar antes qual é a versão da tupla (`xmin`, ~0,3 ms) e reaproveitar a
linha já materializada enquanto ela não mudar.

O TTL é rede de segurança: `xmin` é reescrito em todo UPDATE, mas `VACUUM
FREEZE` normaliza tuplas antigas para o mesmo valor, então nenhuma leitura fica
presa a uma versão por tempo indeterminado.
"""

from __future__ import annotations

import threading
import time
from typing import Any

DEFAULT_TTL_SECONDS = 300.0

_lock = threading.Lock()
# branch → (monotonic_deadline, row_version, row)
_CACHE: dict[str, tuple[float, str, dict[str, Any]]] = {}


def clear_snapshot_row_cache(branch: str | None = None) -> None:
    """Invalida o cache (uma filial ou a plataforma)."""
    with _lock:
        if branch is None:
            _CACHE.clear()
            return
        _CACHE.pop(str(branch).strip(), None)


def get_snapshot_row_cache(branch: str, *, row_version: str) -> dict[str, Any] | None:
    """Linha já materializada, se a versão da tupla continuar a mesma."""
    key = str(branch).strip()
    version = str(row_version or "").strip()
    if not key or not version:
        return None
    now = time.monotonic()
    with _lock:
        hit = _CACHE.get(key)
        if hit is None:
            return None
        deadline, cached_version, row = hit
        if now >= deadline or cached_version != version:
            _CACHE.pop(key, None)
            return None
        return row


def put_snapshot_row_cache(
    branch: str,
    *,
    row_version: str | None,
    row: dict[str, Any],
    ttl_seconds: float = DEFAULT_TTL_SECONDS,
) -> None:
    key = str(branch).strip()
    version = str(row_version or "").strip()
    if not key:
        return
    if not version:
        # Sem versão não há como saber se a linha envelheceu.
        clear_snapshot_row_cache(key)
        return
    deadline = time.monotonic() + max(0.0, float(ttl_seconds))
    with _lock:
        _CACHE[key] = (deadline, version, row)
