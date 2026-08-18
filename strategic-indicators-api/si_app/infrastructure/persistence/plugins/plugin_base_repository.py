from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterable, Iterator

from psycopg import Connection

from si_app.infrastructure.providers.database.plugins_postgres_connection import (
    acquire_plugins_connection,
    current_plugins_lease,
    release_plugins_connection,
)

logger = logging.getLogger(__name__)


class PluginsRepositoryError(RuntimeError):
    pass


class PluginBaseRepository:
    """Base PostgreSQL plugins: pool acquire/release por operação."""

    def __init__(self, connection: Connection[dict[str, Any]] | None = None) -> None:
        self._injected_connection = connection

    @contextmanager
    def db(self) -> Iterator[Connection[dict[str, Any]]]:
        if self._injected_connection is not None:
            yield self._injected_connection
            return

        connection = acquire_plugins_connection()
        discard = False
        try:
            yield connection
        except Exception:
            try:
                connection.rollback()
            except Exception:
                discard = True
            raise
        finally:
            release_plugins_connection(connection, discard=discard)

    @property
    def connection(self) -> Connection[dict[str, Any]]:
        if self._injected_connection is not None:
            return self._injected_connection
        leased = current_plugins_lease()
        if leased is None:
            raise PluginsRepositoryError(
                "Conexão plugins sem lease ativo; use 'with self.db()'."
            )
        return leased

    @property
    def _connection(self) -> Connection[dict[str, Any]]:
        return self.connection

    def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> dict[str, Any] | None:
        try:
            with self.db() as connection:
                with connection.cursor() as cursor:
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
            with self.db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                    return [dict(row) for row in cursor.fetchall()]
        except Exception as exc:
            logger.exception("fetch_all failed")
            raise PluginsRepositoryError("Falha ao listar registros.") from exc

    def _should_auto_commit(self, auto_commit: bool | None) -> bool:
        if auto_commit is None:
            return self._injected_connection is None
        return auto_commit

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool | None = None,
    ) -> None:
        should_commit = self._should_auto_commit(auto_commit)
        try:
            with self.db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                if should_commit:
                    connection.commit()
        except Exception as exc:
            logger.exception("execute failed")
            raise PluginsRepositoryError(f"Falha ao executar comando: {exc}") from exc

    def execute_returning_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool | None = None,
    ) -> dict[str, Any] | None:
        should_commit = self._should_auto_commit(auto_commit)
        try:
            with self.db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                    row = cursor.fetchone()
                if should_commit:
                    connection.commit()
                return dict(row) if row is not None else None
        except Exception as exc:
            logger.exception("execute_returning_one failed")
            raise PluginsRepositoryError(f"Falha ao gravar registro: {exc}") from exc

    def execute_many(
        self,
        query: str,
        values: Iterable[tuple[Any, ...]],
        *,
        auto_commit: bool | None = None,
    ) -> None:
        should_commit = self._should_auto_commit(auto_commit)
        try:
            with self.db() as connection:
                with connection.cursor() as cursor:
                    cursor.executemany(query, values)
                if should_commit:
                    connection.commit()
        except Exception as exc:
            logger.exception("execute_many failed")
            raise PluginsRepositoryError("Falha ao executar múltiplos comandos.") from exc

    def commit(self) -> None:
        try:
            with self.db() as connection:
                connection.commit()
        except Exception as exc:
            logger.exception("commit failed")
            raise PluginsRepositoryError("Falha ao confirmar transação.") from exc

    def rollback(self) -> None:
        try:
            with self.db() as connection:
                connection.rollback()
        except Exception as exc:
            logger.exception("rollback failed")
            raise PluginsRepositoryError("Falha ao desfazer transação.") from exc
