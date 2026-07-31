"""Repository — ordens de produção PCP."""

from __future__ import annotations

from typing import Any

from app.domain.ports.production.pcp_orders_repository_port import PcpOrdersRepositoryPort
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.production.pcp_orders_sql import (
    build_items_count_query,
    build_items_query,
    build_ranking_query,
    build_summary_query,
)


class PcpOrdersRepository(BaseRepository, PcpOrdersRepositoryPort):
    def get_summary(self, **filters: Any) -> dict[str, Any]:
        query, params = build_summary_query(**filters)
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else {}

    def count_items(self, **filters: Any) -> int:
        query, params = build_items_count_query(**filters)
        with self:
            rows = self.execute_query(query, params)
        if not rows:
            return 0
        return int(rows[0].get("total") or 0)

    def get_items(
        self,
        *,
        sort: str,
        offset: int,
        page_size: int,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        query, params = build_items_query(
            sort=sort, offset=offset, page_size=page_size, **filters
        )
        with self:
            return self.execute_query(query, params) or []

    def get_ranking(
        self,
        *,
        rank_by: str,
        metric: str,
        limit: int,
        **filters: Any,
    ) -> list[dict[str, Any]]:
        query, params = build_ranking_query(
            rank_by=rank_by, metric=metric, limit=limit, **filters
        )
        with self:
            return self.execute_query(query, params) or []
