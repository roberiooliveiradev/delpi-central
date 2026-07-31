"""Repository — horas improdutivas."""

from __future__ import annotations

from app.domain.ports.production.unproductive_hours_repository_port import (
    UnproductiveHoursRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.production.unproductive_hours_sql import (
    build_items_count_query,
    build_items_query,
    build_ranking_query,
    build_summary_query,
    build_top_operator_query,
    build_top_resource_query,
)


class UnproductiveHoursRepository(BaseRepository, UnproductiveHoursRepositoryPort):
    def get_summary(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> dict:
        query, params = build_summary_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            stop_reason=stop_reason,
            resource=resource,
            cost_center=cost_center,
            operator_code=operator_code,
        )
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else {}

    def get_top_resource(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> dict | None:
        query, params = build_top_resource_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            stop_reason=stop_reason,
            resource=resource,
            cost_center=cost_center,
            operator_code=operator_code,
        )
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else None

    def get_top_operator(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> dict | None:
        query, params = build_top_operator_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            stop_reason=stop_reason,
            resource=resource,
            cost_center=cost_center,
            operator_code=operator_code,
        )
        with self:
            rows = self.execute_query(query, params)
        return rows[0] if rows else None

    def get_ranking(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        rank_by: str,
        metric: str,
        limit: int,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> list[dict]:
        query, params = build_ranking_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            rank_by=rank_by,
            metric=metric,
            limit=limit,
            stop_reason=stop_reason,
            resource=resource,
            cost_center=cost_center,
            operator_code=operator_code,
        )
        with self:
            return self.execute_query(query, params)

    def count_items(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> int:
        query, params = build_items_count_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            stop_reason=stop_reason,
            resource=resource,
            cost_center=cost_center,
            operator_code=operator_code,
        )
        with self:
            rows = self.execute_query(query, params)
        if not rows:
            return 0
        return int(rows[0].get("total") or 0)

    def get_items(
        self,
        *,
        start_date: str,
        end_date: str,
        branch: str | None,
        sort: str,
        offset: int,
        page_size: int,
        stop_reason: str | None = None,
        resource: str | None = None,
        cost_center: str | None = None,
        operator_code: str | None = None,
    ) -> list[dict]:
        query, params = build_items_query(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            sort=sort,
            offset=offset,
            page_size=page_size,
            stop_reason=stop_reason,
            resource=resource,
            cost_center=cost_center,
            operator_code=operator_code,
        )
        with self:
            return self.execute_query(query, params)
