"""Repository — conjuntos de ordens de produção incompletos (SC2010 x SG1010)."""

from __future__ import annotations

from typing import Any

from app.composition.query_cache_composer import build_query_cache
from app.domain.ports.production.production_order_sets_repository_port import (
    ProductionOrderSetsRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.production.production_order_sets_sql import (
    build_incomplete_sets_query,
    build_incomplete_sets_summary_query,
)

# A recursão da estrutura sobre todos os PAs abertos da filial custa ~1 s; o PCP
# abre a análise em ciclos curtos, então o cache é o que segura o banco.
_CACHE_NS = "production-order-sets-incomplete-v2"


def _cache_key(scope: str, params: tuple) -> str:
    return "|".join([_CACHE_NS, scope, *(str(item) for item in params)])


class ProductionOrderSetsRepository(BaseRepository, ProductionOrderSetsRepositoryPort):
    """As consultas são batches com tabelas temporárias — daí ``execute_batch_query``."""

    def get_incomplete_sets_summary(
        self,
        *,
        branch: str | None,
        issued_from: str | None = None,
    ) -> dict[str, Any]:
        query, params = build_incomplete_sets_summary_query(
            branch=branch, issued_from=issued_from
        )
        key = _cache_key("summary", params)
        cached = build_query_cache().get(key)
        if isinstance(cached, dict):
            return cached

        with self:
            rows = self.execute_batch_query(query, params) or []
        summary = rows[0] if rows else {}
        build_query_cache().set(key, summary)
        return summary

    def get_incomplete_sets(
        self,
        *,
        offset: int,
        page_size: int,
        branch: str | None,
        issued_from: str | None = None,
    ) -> list[dict[str, Any]]:
        query, params = build_incomplete_sets_query(
            offset=offset,
            page_size=page_size,
            branch=branch,
            issued_from=issued_from,
        )
        key = _cache_key("items", params)
        cached = build_query_cache().get(key)
        if isinstance(cached, list):
            return cached

        with self:
            rows = self.execute_batch_query(query, params) or []
        build_query_cache().set(key, rows)
        return rows
