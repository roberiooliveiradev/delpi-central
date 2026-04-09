from __future__ import annotations

import logging
from dataclasses import dataclass
from threading import Lock
from typing import Any

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from app.config import settings

logger = logging.getLogger(__name__)

_connection_lock = Lock()
_cached_connection: Connection[dict[str, Any]] | None = None


class PortalRhDatabaseConfigError(RuntimeError):
    """Erro de configuração do datasource do Portal RH."""


class PortalRhDatabaseConnectionError(RuntimeError):
    """Erro de conexão com o PostgreSQL do Portal RH."""


@dataclass(frozen=True)
class PortalRhDbSettings:
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


def get_portal_rh_connection_settings() -> PortalRhDbSettings:
    host = (settings.PORTAL_RH_DB_HOST or "").strip()
    port_raw = (settings.PORTAL_RH_DB_PORT or "").strip()
    database = (settings.PORTAL_RH_DB_NAME or "").strip()
    user = (settings.PORTAL_RH_DB_USER or "").strip()
    password = (settings.PORTAL_RH_DB_PASSWORD or "").strip()

    if not host:
        raise PortalRhDatabaseConfigError("PORTAL_RH_DB_HOST ausente ou vazio.")
    if not port_raw:
        raise PortalRhDatabaseConfigError("PORTAL_RH_DB_PORT ausente ou vazio.")
    if not database:
        raise PortalRhDatabaseConfigError("PORTAL_RH_DB_NAME ausente ou vazio.")
    if not user:
        raise PortalRhDatabaseConfigError("PORTAL_RH_DB_USER ausente ou vazio.")
    if not password:
        raise PortalRhDatabaseConfigError("PORTAL_RH_DB_PASSWORD ausente ou vazio.")

    try:
        port = int(port_raw)
    except ValueError as exc:
        raise PortalRhDatabaseConfigError(
            "PORTAL_RH_DB_PORT deve ser um inteiro válido."
        ) from exc

    connect_timeout = int(settings.PORTAL_RH_DB_CONNECT_TIMEOUT or "5")
    sslmode = (settings.PORTAL_RH_DB_SSLMODE or "prefer").strip() or "prefer"

    return PortalRhDbSettings(
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


def get_portal_rh_connection() -> Connection[dict[str, Any]]:
    global _cached_connection

    if _is_connection_usable(_cached_connection):
        return _cached_connection  # type: ignore[return-value]

    with _connection_lock:
        if _is_connection_usable(_cached_connection):
            return _cached_connection  # type: ignore[return-value]

        db_settings = get_portal_rh_connection_settings()

        try:
            logger.info(
                "Opening Portal RH PostgreSQL connection.",
                extra={
                    "db_host": db_settings.host,
                    "db_port": db_settings.port,
                    "db_name": db_settings.database,
                },
            )

            connection = psycopg.connect(
                conninfo=db_settings.dsn,
                row_factory=dict_row,
                autocommit=False,
            )

            _cached_connection = connection
            return connection
        except Exception as exc:
            logger.exception(
                "Failed to connect to Portal RH PostgreSQL database.",
                extra={
                    "db_host": db_settings.host,
                    "db_port": db_settings.port,
                    "db_name": db_settings.database,
                },
            )
            raise PortalRhDatabaseConnectionError(
                "Não foi possível conectar ao banco PostgreSQL do Portal RH."
            ) from exc


def close_portal_rh_connection() -> None:
    global _cached_connection

    with _connection_lock:
        if _cached_connection is None:
            return

        try:
            if not _cached_connection.closed:
                _cached_connection.close()
                logger.info("Portal RH PostgreSQL connection closed.")
        finally:
            _cached_connection = None