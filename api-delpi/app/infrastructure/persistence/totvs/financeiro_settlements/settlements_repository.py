"""TOTVS repository for financial settlement events (FK1/FK2)."""

from __future__ import annotations

from app.domain.ports.financeiro_settlements.settlements_repository_port import (
    SettlementsRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

from . import settlements_sql


class SettlementsRepository(BaseRepository, SettlementsRepositoryPort):
    def list_settlements(
        self,
        *,
        side: str,
        start_date: str,
        end_date: str,
        nature_code: str | None = None,
        movement_type: str | None = None,
        sort_by: str,
        sort_dir: str,
        page: int,
        page_size: int,
    ) -> list[dict]:
        query, params = settlements_sql.build_settlements_list_query(
            side=side,
            start_date=start_date,
            end_date=end_date,
            nature_code=nature_code,
            movement_type=movement_type,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        with self:
            return self.execute_query(query, params)

    def count_settlements(
        self,
        *,
        side: str,
        start_date: str,
        end_date: str,
        nature_code: str | None = None,
        movement_type: str | None = None,
    ) -> int:
        query, params = settlements_sql.build_settlements_count_query(
            side=side,
            start_date=start_date,
            end_date=end_date,
            nature_code=nature_code,
            movement_type=movement_type,
        )
        with self:
            row = self.execute_one(query, params)
        if not row:
            return 0
        return int(row.get("total_items") or 0)

    def quality_counters(
        self,
        *,
        side: str,
        start_date: str,
        end_date: str,
        nature_code: str | None = None,
        movement_type: str | None = None,
    ) -> dict:
        query, params = settlements_sql.build_settlements_quality_query(
            side=side,
            start_date=start_date,
            end_date=end_date,
            nature_code=nature_code,
            movement_type=movement_type,
        )
        with self:
            return self.execute_one(query, params) or {
                "total_events": 0,
                "missing_document": 0,
                "missing_nature": 0,
                "unresolved_branch": 0,
            }

    def summary_groups(
        self,
        *,
        start_date: str,
        end_date: str,
        nature_code: str | None = None,
        movement_type: str | None = None,
    ) -> list[dict]:
        query, params = settlements_sql.build_settlements_summary_query(
            start_date=start_date,
            end_date=end_date,
            nature_code=nature_code,
            movement_type=movement_type,
        )
        with self:
            return self.execute_query(query, params)

    def nature_descriptions(
        self, *, nature_codes: tuple[str, ...]
    ) -> dict[str, str]:
        if not nature_codes:
            return {}
        query, params = settlements_sql.build_nature_descriptions_query(
            nature_codes=nature_codes
        )
        with self:
            rows = self.execute_query(query, params)
        return {
            row["nature_code"]: row.get("nature_description") or ""
            for row in rows
        }

    def movement_descriptions(
        self, *, movement_types: tuple[str, ...]
    ) -> dict[str, str]:
        if not movement_types:
            return {}
        query, params = settlements_sql.build_movement_descriptions_query(
            movement_types=movement_types
        )
        with self:
            rows = self.execute_query(query, params)
        return {
            row["movement_type"]: row.get("movement_description") or ""
            for row in rows
        }
