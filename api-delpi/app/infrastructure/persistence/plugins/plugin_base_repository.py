# app/infrastructure/persistence/plugins/plugin_base_repository.py
from __future__ import annotations

import logging
from typing import Any, Iterable

from psycopg import Connection

from app.infrastructure.providers.databse.plugins_postgres_connection import get_plugins_connection

logger = logging.getLogger(__name__)


class PluginsRepositoryError(RuntimeError):
    """Erro base de persistência do contexto plugins."""


class PluginBaseRepository:
    """
    Base para repositórios PostgreSQL do contexto plugins.

    Regras:
    - não contém regra de domínio
    - não conhece HTTP/Flask
    - não mistura SQL Server/TOTVS com PostgreSQL
    """

    def __init__(self, connection: Connection[dict[str, Any]] | None = None) -> None:
        self._connection: Connection[dict[str, Any]] = (
            connection if connection is not None else get_plugins_connection()
        )

    @property
    def connection(self) -> Connection[dict[str, Any]]:
        return self._connection

    def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                row = cursor.fetchone()
                return dict(row) if row is not None else None
        except Exception as exc:
            logger.exception(
                "Plugins repository fetch_one failed.",
                extra={"query": query},
            )
            raise PluginsRepositoryError(
                "Falha ao executar fetch_one no banco de plugins."
            ) from exc

    def fetch_all(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as exc:
            logger.exception(
                "Plugins repository fetch_all failed.",
                extra={"query": query},
            )
            raise PluginsRepositoryError(
                "Falha ao executar fetch_all no banco de plugins."
            ) from exc

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = False,
    ) -> None:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())

            if auto_commit:
                self.commit()
        except Exception as exc:
            self.rollback()
            logger.exception(
                "Plugins repository execute failed.",
                extra={"query": query},
            )
            raise PluginsRepositoryError(
                "Falha ao executar comando no banco de plugins."
            ) from exc

    def execute_returning_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = False,
    ) -> dict[str, Any] | None:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                row = cursor.fetchone()

            if auto_commit:
                self.commit()

            return dict(row) if row is not None else None
        except Exception as exc:
            self.rollback()
            logger.exception(
                "Plugins repository execute_returning_one failed.",
                extra={"query": query},
            )
            raise PluginsRepositoryError(
                "Falha ao executar comando com retorno no banco de plugins."
            ) from exc

    def execute_many(
        self,
        query: str,
        values: Iterable[tuple[Any, ...]],
        *,
        auto_commit: bool = False,
    ) -> None:
        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(query, values)

            if auto_commit:
                self.commit()
        except Exception as exc:
            self.rollback()
            logger.exception(
                "Plugins repository execute_many failed.",
                extra={"query": query},
            )
            raise PluginsRepositoryError(
                "Falha ao executar múltiplos comandos no banco de plugins."
            ) from exc

    def commit(self) -> None:
        try:
            self.connection.commit()
        except Exception as exc:
            logger.exception("Plugins repository commit failed.")
            raise PluginsRepositoryError(
                "Falha ao confirmar transação no banco de plugins."
            ) from exc

    def rollback(self) -> None:
        try:
            self.connection.rollback()
        except Exception as exc:
            logger.exception("Plugins repository rollback failed.")
            raise PluginsRepositoryError(
                "Falha ao desfazer transação no banco de plugins."
            ) from exc