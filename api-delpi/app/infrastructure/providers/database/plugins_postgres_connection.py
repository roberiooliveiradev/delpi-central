# app/infrastructure/providers/database/plugins_postgres_connection.py
from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

_thread_local = threading.local()
_registry_lock = threading.Lock()
_registered_connections: set[Connection[dict[str, Any]]] = set()


class PluginsDatabaseConfigError(RuntimeError):
    """Erro de configuração do datasource de plugins."""


class PluginsDatabaseConnectionError(RuntimeError):
    """Erro de conexão com o PostgreSQL do contexto plugins."""


@dataclass(frozen=True)
class PluginsDbSettings:
    host: str
    port: int
    database: str
    user: str
    password: str
    connect_timeout: int = 5
    sslmode: str = "prefer"

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.database} "
            f"user={self.user} "
            f"password={self.password} "
            f"connect_timeout={self.connect_timeout} "
            f"sslmode={self.sslmode}"
        )


def _read_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise PluginsDatabaseConfigError(
            f"Variável obrigatória ausente ou vazia: {name}"
        )
    return value


def get_plugins_connection_settings() -> PluginsDbSettings:
    """
    Lê e valida as variáveis de ambiente do datasource de plugins.
    """
    host = _read_required_env("PLUGINS_DB_HOST")
    port_raw = _read_required_env("PLUGINS_DB_PORT")
    database = _read_required_env("PLUGINS_DB_NAME")
    user = _read_required_env("PLUGINS_DB_USER")
    password = _read_required_env("PLUGINS_DB_PASSWORD")

    try:
        port = int(port_raw)
    except ValueError as exc:
        raise PluginsDatabaseConfigError(
            "PLUGINS_DB_PORT deve ser um número inteiro válido."
        ) from exc

    connect_timeout = int(os.getenv("PLUGINS_DB_CONNECT_TIMEOUT", "5"))
    sslmode = os.getenv("PLUGINS_DB_SSLMODE", "prefer").strip() or "prefer"

    return PluginsDbSettings(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        connect_timeout=connect_timeout,
        sslmode=sslmode,
    )


def _is_connection_usable(
    connection: Connection[dict[str, Any]] | None,
) -> bool:
    if connection is None:
        return False

    try:
        return not connection.closed
    except Exception:
        return False


def _open_plugins_connection() -> Connection[dict[str, Any]]:
    settings = get_plugins_connection_settings()
    try:
        logger.info(
            "Opening plugins PostgreSQL connection.",
            extra={
                "db_host": settings.host,
                "db_port": settings.port,
                "db_name": settings.database,
                "thread": threading.current_thread().name,
            },
        )
        return psycopg.connect(
            conninfo=settings.dsn,
            row_factory=dict_row,
            autocommit=False,
        )
    except Exception as exc:
        logger.exception(
            "Failed to connect to plugins PostgreSQL database.",
            extra={
                "db_host": settings.host,
                "db_port": settings.port,
                "db_name": settings.database,
            },
        )
        raise PluginsDatabaseConnectionError(
            "Não foi possível conectar ao banco PostgreSQL de plugins."
        ) from exc


def get_plugins_connection() -> Connection[dict[str, Any]]:
    """
    Retorna uma conexão PostgreSQL reutilizável **por thread**.

    Requests concorrentes (uvicorn threadpool) não podem compartilhar a mesma
    Connection psycopg: UniqueViolation/rollback em um request aborta o outro
    (InFailedSqlTransaction) e pode desfazer INSERT ainda não commitado.
    """
    connection = getattr(_thread_local, "connection", None)
    if _is_connection_usable(connection):
        return connection  # type: ignore[return-value]

    connection = _open_plugins_connection()
    _thread_local.connection = connection
    with _registry_lock:
        _registered_connections.add(connection)
    return connection


def close_plugins_connection() -> None:
    """
    Fecha todas as conexões de plugins registradas (shutdown / testes).
    """
    with _registry_lock:
        connections = list(_registered_connections)
        _registered_connections.clear()

    for connection in connections:
        try:
            if not connection.closed:
                connection.close()
        except Exception:
            logger.exception("Failed to close plugins PostgreSQL connection.")

    _thread_local.connection = None
    logger.info("Plugins PostgreSQL connections closed.")


def check_plugins_connection() -> bool:
    """
    Executa uma verificação simples de conectividade.
    """
    connection = get_plugins_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 AS ok;")
            row = cursor.fetchone()

        return bool(row and row.get("ok") == 1)
    except Exception:
        logger.exception("Plugins PostgreSQL healthcheck failed.")
        return False
