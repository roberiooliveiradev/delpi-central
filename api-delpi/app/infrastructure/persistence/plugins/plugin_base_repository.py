# app/infrastructure/persistence/plugins/plugin_base_repository.py

from __future__ import annotations

import functools
import logging
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Iterable, TypeVar

from psycopg import Connection
from psycopg.errors import UndefinedColumn, UndefinedTable

from app.infrastructure.providers.database.plugins_postgres_connection import (
    acquire_plugins_connection,
    current_plugins_lease,
    release_plugins_connection,
)

logger = logging.getLogger(__name__)

_SCHEMA_OUTDATED_MESSAGE = (
    "Schema do banco de plugins desatualizado. "
    "No container api-delpi: "
    "python scripts/run_plugins_migrations.py status "
    "e depois up --plugin <slug> (nunca reset em produção)."
)


class PluginsRepositoryError(RuntimeError):
    """Erro base de persistência do contexto plugins."""


class PluginsSchemaOutdatedError(PluginsRepositoryError):
    """Código espera colunas/tabelas que as migrations ainda não aplicaram."""


_F = TypeVar("_F", bound=Callable[..., Any])


def plugins_unit_of_work(method: _F) -> _F:
    """Mantém um lease único durante writes multi-statement.

    ``execute(auto_commit=False)`` sem lease externo devolve a conexão ao
    pool, que faz ``rollback()`` — o ``commit()`` posterior não persiste e a
    API pode devolver sucesso. O padrão explícito equivalente é
    ``with self.db():`` (LNF, Auditoria 5S, Kaizen).
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if getattr(self, "_injected_connection", None) is not None:
            return method(self, *args, **kwargs)
        if current_plugins_lease() is not None:
            return method(self, *args, **kwargs)
        with self.db():
            return method(self, *args, **kwargs)

    wrapper.__plugins_unit_of_work__ = True  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]


def wrap_plugins_db_error(operation: str, exc: BaseException) -> PluginsRepositoryError:
    """Mapeia falhas de SQL do plugins DB para erros tipados."""
    if isinstance(exc, (UndefinedColumn, UndefinedTable)):
        detail = str(exc).strip().split("\n", 1)[0]
        logger.error(
            "Plugins schema outdated during %s: %s",
            operation,
            detail,
        )
        return PluginsSchemaOutdatedError(_SCHEMA_OUTDATED_MESSAGE)
    return PluginsRepositoryError(
        f"Falha ao executar {operation} no banco de plugins."
    )


class PluginBaseRepository:
    """
    Base para repositórios PostgreSQL do contexto plugins.

    Regras:
    - não contém regra de domínio
    - não conhece HTTP/Flask
    - não mistura SQL Server/TOTVS com PostgreSQL
    - conexão via pool (acquire/release); lease aninhável na thread
    """

    def __init__(self, connection: Connection[dict[str, Any]] | None = None) -> None:
        # Injetado só em testes / geradores que já possuem lease.
        self._injected_connection = connection

    @contextmanager
    def db(self) -> Iterator[Connection[dict[str, Any]]]:
        """Unidade de trabalho: adquire do pool (ou reusa lease externo)."""
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
            logger.exception(
                "Plugins repository fetch_one failed.",
                extra={"query": query},
            )
            raise wrap_plugins_db_error("fetch_one", exc) from exc

    def fetch_all(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
    ) -> list[dict[str, Any]]:
        try:
            with self.db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]
        except Exception as exc:
            logger.exception(
                "Plugins repository fetch_all failed.",
                extra={"query": query},
            )
            raise wrap_plugins_db_error("fetch_all", exc) from exc

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> None:
        """Executa SQL. ``auto_commit=False`` exige lease externo
        (``with self.db():`` / ``@plugins_unit_of_work``); sem isso o pool
        faz rollback ao devolver a conexão.
        """
        try:
            with self.db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                if auto_commit:
                    connection.commit()
        except Exception as exc:
            logger.exception(
                "Plugins repository execute failed.",
                extra={"query": query},
            )
            raise wrap_plugins_db_error("comando", exc) from exc

    def execute_returning_one(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        *,
        auto_commit: bool = True,
    ) -> dict[str, Any] | None:
        try:
            with self.db() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(query, params or ())
                    row = cursor.fetchone()
                if auto_commit:
                    connection.commit()
                return dict(row) if row is not None else None
        except Exception as exc:
            logger.exception(
                "Plugins repository execute_returning_one failed.",
                extra={"query": query},
            )
            raise wrap_plugins_db_error("comando com retorno", exc) from exc

    def execute_many(
        self,
        query: str,
        values: Iterable[tuple[Any, ...]],
        *,
        auto_commit: bool = True,
    ) -> None:
        try:
            with self.db() as connection:
                with connection.cursor() as cursor:
                    cursor.executemany(query, values)
                if auto_commit:
                    connection.commit()
        except Exception as exc:
            logger.exception(
                "Plugins repository execute_many failed.",
                extra={"query": query},
            )
            raise wrap_plugins_db_error("múltiplos comandos", exc) from exc

    def commit(self) -> None:
        try:
            with self.db() as connection:
                connection.commit()
        except Exception as exc:
            logger.exception("Plugins repository commit failed.")
            raise PluginsRepositoryError(
                "Falha ao confirmar transação no banco de plugins."
            ) from exc

    def rollback(self) -> None:
        try:
            with self.db() as connection:
                connection.rollback()
        except Exception as exc:
            logger.exception("Plugins repository rollback failed.")
            raise PluginsRepositoryError(
                "Falha ao desfazer transação no banco de plugins."
            ) from exc
