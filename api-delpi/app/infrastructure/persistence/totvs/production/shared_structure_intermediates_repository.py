"""Repository — intermediários compartilhados entre PAs ativos."""

from __future__ import annotations

from typing import Any

from app.composition.query_cache_composer import build_query_cache
from app.domain.ports.production.shared_structure_intermediates_repository_port import (
    SharedStructureIntermediatesRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.production.shared_structure_intermediates_sql import (
    build_shared_intermediates_query,
    build_shared_intermediates_summary_query,
)

_CACHE_NS = "production-shared-structure-intermediates-v1"


def _cache_key(namespace: str, scope: str, params: tuple) -> str:
    return "|".join([namespace, scope, *(str(item) for item in params)])


class SharedStructureIntermediatesRepository(
    BaseRepository, SharedStructureIntermediatesRepositoryPort
):
    def get_shared_intermediates_summary(
        self,
        *,
        branch: str | None,
        movement_from: str,
        movement_to_exclusive: str,
    ) -> dict[str, Any]:
        query, params = build_shared_intermediates_summary_query(
            branch=branch,
            movement_from=movement_from,
            movement_to_exclusive=movement_to_exclusive,
        )
        key = _cache_key(_CACHE_NS, "summary", params)
        cached = build_query_cache().get(key)
        if isinstance(cached, dict):
            return cached

        with self:
            rows = self.execute_batch_query(query, params) or []
        summary = rows[0] if rows else {}
        build_query_cache().set(key, summary)
        return summary

    def get_shared_intermediates(
        self,
        *,
        offset: int,
        page_size: int,
        branch: str | None,
        movement_from: str,
        movement_to_exclusive: str,
    ) -> list[dict[str, Any]]:
        query, params = build_shared_intermediates_query(
            offset=offset,
            page_size=page_size,
            branch=branch,
            movement_from=movement_from,
            movement_to_exclusive=movement_to_exclusive,
        )
        key = _cache_key(_CACHE_NS, "items", params)
        cached = build_query_cache().get(key)
        if isinstance(cached, list):
            return cached

        with self:
            rows = self.execute_batch_query(query, params) or []
        build_query_cache().set(key, rows)
        return rows
