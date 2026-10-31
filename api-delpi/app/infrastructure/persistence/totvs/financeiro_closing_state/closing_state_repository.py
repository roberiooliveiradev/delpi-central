"""TOTVS repository for the R12/R15 closing-state markers."""

from __future__ import annotations

from app.domain.ports.financeiro_closing_state.closing_state_repository_port import (
    ClosingStateRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import (
    BaseRepository,
)

from . import closing_state_sql


class ClosingStateRepository(BaseRepository, ClosingStateRepositoryPort):
    def snapshot_branch_counts(
        self, *, snapshot_date: str, branches: tuple[str, ...]
    ) -> dict[str, int]:
        query, params = closing_state_sql.build_snapshot_branch_counts_query(
            snapshot_date=snapshot_date, branches=branches
        )
        with self:
            rows = self.execute_query(query, params)
        return {
            str(row.get("branch_code") or "").strip(): int(
                row.get("row_count") or 0
            )
            for row in rows
        }

    def last_snapshot_dates(
        self, *, branches: tuple[str, ...]
    ) -> dict[str, str]:
        query, params = closing_state_sql.build_last_snapshot_dates_query(
            branches=branches
        )
        with self:
            rows = self.execute_query(query, params)
        return {
            str(row.get("branch_code") or "").strip(): str(
                row.get("last_snapshot_date") or ""
            ).strip()
            for row in rows
        }

    def mv_ulmes_values(
        self, *, branches: tuple[str, ...]
    ) -> dict[str, str]:
        query, params = closing_state_sql.build_mv_ulmes_query(
            branches=branches
        )
        with self:
            rows = self.execute_query(query, params)
        return {
            str(row.get("branch_code") or "").strip(): str(
                row.get("param_value") or ""
            ).strip()
            for row in rows
        }

    def ttat_write_window(
        self,
        *,
        log_table: str,
        field_name: str,
        window_start: str,
        window_end: str,
    ) -> dict:
        query, params = closing_state_sql.build_ttat_write_window_query(
            log_table=log_table,
            field_name=field_name,
            window_start=window_start,
            window_end=window_end,
        )
        with self:
            return self.execute_one(query, params) or {}
