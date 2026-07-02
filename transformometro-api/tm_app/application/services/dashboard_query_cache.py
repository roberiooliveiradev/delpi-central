from __future__ import annotations

import threading
import time
from typing import Any, Callable

from tm_app.config import settings


class DashboardQueryCache:
    """Cache de resultado das consultas do dashboard calculadas em tempo real.

    A fonte de verdade do dashboard é o motor live (``DashboardCalculatorService``
    sobre o cadastro). Este cache guarda o **resultado** de cada consulta por uma
    janela curta (TTL) para evitar recomputar a mesma coisa em polling/integrações
    sobre a conexão Postgres única compartilhada.

    Invalidação é por **geração**: qualquer mutação de CRUD chama ``invalidate()``,
    que incrementa o contador e descarta tudo em O(1) — sem recálculo pesado no
    caminho de escrita. A próxima leitura recomputa preguiçosamente e recacheia.

    Thread-safe: o cálculo roda fora do lock (pode tocar o banco); o resultado só é
    gravado se a geração não mudou durante o cálculo (evita cachear valor obsoleto
    quando um CRUD ocorre no meio de uma leitura).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, tuple[int, float, Any]] = {}
        self._generation = 0
        self._hits = 0
        self._misses = 0
        self._invalidations = 0

    @property
    def enabled(self) -> bool:
        return bool(settings.TM_DASHBOARD_QUERY_CACHE)

    @property
    def ttl_seconds(self) -> float:
        return float(settings.TM_DASHBOARD_QUERY_CACHE_TTL_SECONDS)

    def get_or_compute(
        self,
        namespace: str,
        key: Any,
        compute: Callable[[], Any],
    ) -> Any:
        if not self.enabled:
            return compute()

        cache_key = self._build_key(namespace, key)
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(cache_key)
            if entry is not None:
                generation, expires_at, value = entry
                if generation == self._generation and now < expires_at:
                    self._hits += 1
                    return value
            start_generation = self._generation

        value = compute()

        with self._lock:
            self._misses += 1
            # Só cacheia se nenhuma invalidação ocorreu durante o cálculo.
            if self._generation == start_generation:
                self._store[cache_key] = (
                    self._generation,
                    time.monotonic() + self.ttl_seconds,
                    value,
                )
        return value

    def invalidate(self) -> int:
        """Descarta todo o cache (O(1) lógico) e retorna quantas entradas havia."""
        with self._lock:
            self._generation += 1
            self._invalidations += 1
            cleared = len(self._store)
            self._store.clear()
            return cleared

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "enabled": self.enabled,
                "ttl_seconds": self.ttl_seconds,
                "generation": self._generation,
                "entries": len(self._store),
                "hits": self._hits,
                "misses": self._misses,
                "invalidations": self._invalidations,
            }

    @staticmethod
    def _build_key(namespace: str, key: Any) -> str:
        return f"{namespace}:{key!r}"


dashboard_query_cache = DashboardQueryCache()
