"""Repository — carga máquina (SH8010 alocada por centro de trabalho)."""

from __future__ import annotations

from typing import Any

from app.composition.query_cache_composer import build_query_cache
from app.domain.ports.production.machine_load_repository_port import (
    MachineLoadRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.production.machine_load_sql import (
    build_appointment_status_query,
    build_operations_count_query,
    build_operations_query,
    build_work_centers_query,
)

# A SH8 é reprocessada ~1x/dia e a fila é consultada em polling pelo Portal PCP.
_CACHE_NS = "production-machine-load-v1"


def _cache_key(scope: str, params: tuple, extra: tuple = ()) -> str:
    parts = [_CACHE_NS, scope, *(str(item) for item in params), *(str(item) for item in extra)]
    return "|".join(parts)


class MachineLoadRepository(BaseRepository, MachineLoadRepositoryPort):
    def get_work_centers(self, **filters: Any) -> list[dict[str, Any]]:
        query, params = build_work_centers_query(**filters)
        key = _cache_key("work-centers", params)
        cached = build_query_cache().get(key)
        if isinstance(cached, list):
            return cached

        with self:
            rows = self.execute_query(query, params) or []
        build_query_cache().set(key, rows)
        return rows

    def count_operations(self, **filters: Any) -> int:
        query, params = build_operations_count_query(**filters)
        key = _cache_key("operations-count", params)
        cached = build_query_cache().get(key)
        if isinstance(cached, int):
            return cached

        with self:
            rows = self.execute_query(query, params)
        total = int((rows[0] or {}).get("total") or 0) if rows else 0
        build_query_cache().set(key, total)
        return total

    def get_operations(
        self,
        *,
        sort: str,
        offset: int,
        page_size: int,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        query, params = build_operations_query(
            sort=sort, offset=offset, page_size=page_size, **filters
        )
        key = _cache_key("operations", params, (sort,))
        cached = build_query_cache().get(key)
        if isinstance(cached, list):
            return cached

        with self:
            rows = self.execute_query(query, params) or []
        build_query_cache().set(key, rows)
        return rows

    def get_appointment_status(
        self,
        *,
        branch: str,
        appointment_active_since: str,
        appointment_history_since: str,
    ) -> list[dict[str, Any]]:
        query, params = build_appointment_status_query(
            branch=branch,
            appointment_active_since=appointment_active_since,
            appointment_history_since=appointment_history_since,
        )
        # Status vivo: sem cache — o PCP precisa refletir o chão de fábrica.
        with self:
            return self.execute_query(query, params) or []
