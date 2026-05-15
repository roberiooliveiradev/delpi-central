from __future__ import annotations

import logging
from typing import Any, Iterable

from psycopg import Connection

from si_app.infrastructure.providers.database.portal_rh_postgres_connection import (
    get_portal_rh_connection,
)

logger = logging.getLogger(__name__)


class PortalRhRepositoryError(RuntimeError):
    """Erro base de persistência do Portal RH."""


class PortalRhBaseRepository:
    def __init__(self, connection: Connection[dict[str, Any]] | None = None) -> None:
        self._connection: Connection[dict[str, Any]] = (
            connection if connection is not None else get_portal_rh_connection()
        )

    @property
    def connection(self) -> Connection[dict[str, Any]]:
        return self._connection

    def fetch_one(
        self,
        query: str,
        params: Any | None = None,
    ) -> dict[str, Any] | None:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                row = cursor.fetchone()
                return dict(row) if row is not None else None
        except Exception as exc:
            self.rollback()
            logger.exception(
                "Portal RH repository fetch_one failed.",
                extra={"query": query},
            )
            raise PortalRhRepositoryError(
                f"Falha ao executar fetch_one no banco do Portal RH: {exc}"
            ) from exc

    def fetch_all(
        self,
        query: str,
        params: Any | None = None,
    ) -> list[dict[str, Any]]:
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as exc:
            self.rollback()
            logger.exception(
                "Portal RH repository fetch_all failed.",
                extra={"query": query},
            )
            raise PortalRhRepositoryError(
                "Falha ao executar fetch_all no banco do Portal RH."
            ) from exc

    def execute(
        self,
        query: str,
        params: Any | None = None,
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
                "Portal RH repository execute failed.",
                extra={"query": query},
            )
            raise PortalRhRepositoryError(
                "Falha ao executar comando no banco do Portal RH."
            ) from exc

    def execute_many(
        self,
        query: str,
        values: Iterable[Any],
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
                "Portal RH repository execute_many failed.",
                extra={"query": query},
            )
            raise PortalRhRepositoryError(
                "Falha ao executar múltiplos comandos no banco do Portal RH."
            ) from exc

    def commit(self) -> None:
        try:
            self.connection.commit()
        except Exception as exc:
            logger.exception("Portal RH repository commit failed.")
            raise PortalRhRepositoryError(
                "Falha ao confirmar transação no banco do Portal RH."
            ) from exc

    def rollback(self) -> None:
        try:
            self.connection.rollback()
        except Exception as exc:
            logger.exception("Portal RH repository rollback failed.")
            raise PortalRhRepositoryError(
                "Falha ao desfazer transação no banco do Portal RH."
            ) from exc