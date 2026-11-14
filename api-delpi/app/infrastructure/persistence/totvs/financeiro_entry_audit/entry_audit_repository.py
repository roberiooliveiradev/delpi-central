"""TOTVS repository — entry-audit extracts. Read only."""

from __future__ import annotations

from typing import Any

from app.infrastructure.persistence.totvs.base_repository import BaseRepository

from . import entry_audit_sql


class EntryAuditRepository(BaseRepository):
    def fetch_documents(
        self, *, branch: str, received_from: str, received_to: str, species: list[str], offset: int, page_size: int
    ) -> list[dict[str, Any]]:
        sql, _names = entry_audit_sql.documents_sql(species)
        params = (branch, received_from, received_to, *species, offset, page_size)
        with self:
            return self.execute_query(sql, params)

    def fetch_items(
        self, *, branch: str, received_from: str, received_to: str, species: list[str], offset: int, page_size: int
    ) -> list[dict[str, Any]]:
        sql, _names = entry_audit_sql.items_sql(species)
        params = (branch, received_from, received_to, *species, offset, page_size)
        with self:
            return self.execute_query(sql, params)

    def fetch_fiscal_book(
        self, *, branch: str, received_from: str, received_to: str, species: list[str], offset: int, page_size: int
    ) -> list[dict[str, Any]]:
        sql, _names = entry_audit_sql.fiscal_book_sql(species)
        params = (branch, received_from, received_to, *species, offset, page_size)
        with self:
            return self.execute_query(sql, params)

    def fetch_tes(self, *, offset: int, page_size: int) -> list[dict[str, Any]]:
        with self:
            return self.execute_query(entry_audit_sql.tes_sql(), (offset, page_size))

    def fetch_branches(self) -> list[dict[str, Any]]:
        with self:
            return self.execute_query(entry_audit_sql.branches_sql(), ())
