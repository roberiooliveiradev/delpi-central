"""TOTVS repository — entry-audit extracts. Read only."""

from __future__ import annotations

import os
from typing import Any

import pyodbc

from app.core.exceptions import DatabaseConnectionError
from app.infrastructure.persistence.totvs.base_repository import BaseRepository

from . import entry_audit_sql


def dedicated_entry_audit_host() -> str:
    """Host só da leitura da auditoria. Vazio: o repositório usa o pool geral."""
    return os.getenv("ENTRY_AUDIT_DB_HOST", "").strip()


class EntryAuditRepository(BaseRepository):
    def _connect(self):
        host = dedicated_entry_audit_host()
        if not host:
            return super()._connect()
        database = os.getenv("ENTRY_AUDIT_DB_DATABASE", "").strip()
        user = os.getenv("ENTRY_AUDIT_DB_USER", "").strip()
        password = os.getenv("ENTRY_AUDIT_DB_PASSWORD", "")
        port = os.getenv("ENTRY_AUDIT_DB_PORT", "1433").strip() or "1433"
        if not all([database, user, password]):
            raise DatabaseConnectionError("ENTRY_AUDIT_DB incompleto")
        try:
            self.connection = pyodbc.connect(
                "DRIVER={ODBC Driver 18 for SQL Server};"
                f"SERVER={host},{port};DATABASE={database};UID={user};PWD={password};"
                "Encrypt=no;TrustServerCertificate=yes;",
                timeout=5,
            )
            self.connection.timeout = 30
            self.connection.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
            self.cursor = self.connection.cursor()
            self._dedicated = True
        except Exception as exc:
            self.connection = None
            self.cursor = None
            raise DatabaseConnectionError("Falha na leitura dedicada da auditoria de entradas") from exc

    def _close(self, *, discard: bool = False):
        if not getattr(self, "_dedicated", False):
            return super()._close(discard=discard)
        try:
            if self.cursor:
                self.cursor.close()
        except Exception:
            pass
        finally:
            self.cursor = None
        try:
            if self.connection:
                self.connection.close()
        except Exception:
            pass
        finally:
            self.connection = None
            self._dedicated = False

    def fetch_documents(
        self, *, branch: str, received_from: str, received_to: str, species: list[str], offset: int, page_size: int
    ) -> list[dict[str, Any]]:
        sql, _names = entry_audit_sql.documents_sql(species)
        params = (branch, received_from, received_to, *species, offset, page_size)
        with self:
            return self.execute_query(sql, params)

    def fetch_documents_by_access_keys(
        self, *, branch: str, access_keys: list[str]
    ) -> list[dict[str, Any]]:
        if not access_keys:
            return []
        sql, _names = entry_audit_sql.documents_by_access_keys_sql(len(access_keys))
        params = (branch, *access_keys)
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
