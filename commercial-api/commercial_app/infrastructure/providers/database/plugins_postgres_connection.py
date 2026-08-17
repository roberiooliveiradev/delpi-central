from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from threading import Lock
from typing import Any

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

_connection_lock = Lock()
_cached_connection: Connection[dict[str, Any]] | None = None


class PluginsDatabaseConfigError(RuntimeError):
    pass


class PluginsDatabaseConnectionError(RuntimeError):
    pass


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


def get_plugins_connection_settings() -> PluginsDbSettings:
    def req(name: str) -> str:
        value = os.getenv(name, "").strip()
        if not value:
            raise PluginsDatabaseConfigError(f"Variável obrigatória ausente: {name}")
        return value

    return PluginsDbSettings(
        host=req("PLUGINS_DB_HOST"),
        port=int(req("PLUGINS_DB_PORT")),
        database=req("PLUGINS_DB_NAME"),
        user=req("PLUGINS_DB_USER"),
        password=req("PLUGINS_DB_PASSWORD"),
        connect_timeout=int(os.getenv("PLUGINS_DB_CONNECT_TIMEOUT", "5")),
        sslmode=os.getenv("PLUGINS_DB_SSLMODE", "prefer").strip() or "prefer",
    )


def get_plugins_connection() -> Connection[dict[str, Any]]:
    global _cached_connection

    if _cached_connection is not None and not _cached_connection.closed:
        return _cached_connection

    with _connection_lock:
        if _cached_connection is not None and not _cached_connection.closed:
            return _cached_connection

        settings = get_plugins_connection_settings()
        try:
            _cached_connection = psycopg.connect(
                conninfo=settings.dsn,
                row_factory=dict_row,
                autocommit=False,
            )
            return _cached_connection
        except Exception as exc:
            raise PluginsDatabaseConnectionError(
                "Não foi possível conectar ao postgres-plugins."
            ) from exc
