from __future__ import annotations

import logging
from typing import Any, Iterable

from psycopg import Connection

from maint_app.infrastructure.providers.database.plugins_postgres_connection import (
    get_plugins_connection,
)

logger = logging.getLogger(__name__)


class PluginsRepositoryError(RuntimeError):
    pass


class PluginBaseRepository:
    def __init__(self, connection: Connection[dict[str, Any]] | None = None) -> None:
        self._connection = connection if connection is not None else get_plugins_connection()

    def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None:
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params or ())
                row = cursor.fetchone()
                return dict(row) if row is not None else None
        except Exception as exc:
            logger.exception("fetch_one failed")
            raise PluginsRepositoryError("Falha ao consultar registro.") from exc

    def fetch_all(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params or ())
                return [dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            logger.exception("fetch_all failed")
            raise PluginsRepositoryError("Falha ao listar registros.") from exc

    def execute_returning_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> dict[str, Any] | None:
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params or ())
                row = cursor.fetchone()
            if auto_commit:
                self._connection.commit()
            return dict(row) if row is not None else None
        except Exception as exc:
            self._connection.rollback()
            logger.exception("execute_returning_one failed")
            raise PluginsRepositoryError(f"Falha ao gravar registro: {exc}") from exc

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> None:
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params or ())
            if auto_commit:
                self._connection.commit()
        except Exception as exc:
            self._connection.rollback()
            logger.exception("execute failed")
            raise PluginsRepositoryError(f"Falha ao executar comando: {exc}") from exc
