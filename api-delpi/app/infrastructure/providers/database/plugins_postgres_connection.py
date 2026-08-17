# app/infrastructure/providers/database/plugins_postgres_connection.py
from __future__ import annotations

import logging
import os
import queue
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

PLUGINS_DB_POOL_MAX_SIZE = int(os.getenv("PLUGINS_DB_POOL_MAX_SIZE", "10") or "10")
PLUGINS_DB_POOL_ACQUIRE_TIMEOUT = float(
    os.getenv("PLUGINS_DB_POOL_ACQUIRE_TIMEOUT", "30") or "30"
)
PLUGINS_DB_APPLICATION_NAME = (
    os.getenv("PLUGINS_DB_APPLICATION_NAME", "api-delpi-plugins").strip()
    or "api-delpi-plugins"
)

_pool: PluginsConnectionPool | None = None
_pool_lock = threading.Lock()
_lease_local = threading.local()


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
    application_name: str = "api-delpi-plugins"

    @property
    def dsn(self) -> str:
        return (
            f"host={self.host} "
            f"port={self.port} "
            f"dbname={self.database} "
            f"user={self.user} "
            f"password={self.password} "
            f"connect_timeout={self.connect_timeout} "
            f"sslmode={self.sslmode} "
            f"application_name={self.application_name}"
        )


def _read_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise PluginsDatabaseConfigError(
            f"Variável obrigatória ausente ou vazia: {name}"
        )
    return value


def get_plugins_connection_settings() -> PluginsDbSettings:
    """Lê e valida as variáveis de ambiente do datasource de plugins."""
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
        application_name=PLUGINS_DB_APPLICATION_NAME,
    )


def _open_plugins_connection() -> Connection[dict[str, Any]]:
    settings = get_plugins_connection_settings()
    try:
        logger.debug(
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


class PluginsConnectionPool:
    """Pool limitado de conexões psycopg (espelho do TotvsConnectionPool)."""

    def __init__(self, *, max_size: int) -> None:
        self._max_size = max(1, max_size)
        self._available: queue.Queue[Connection[dict[str, Any]]] = queue.Queue()
        self._created = 0
        self._acquire_timeouts = 0
        self._discards = 0
        self._lock = threading.Lock()

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def created(self) -> int:
        with self._lock:
            return self._created

    def stats(self) -> dict[str, Any]:
        with self._lock:
            created = self._created
            timeouts = self._acquire_timeouts
            discards = self._discards
        available = self._available.qsize()
        in_use = max(0, created - available)
        return {
            "enabled": True,
            "max_size": self._max_size,
            "created": created,
            "available": available,
            "in_use": in_use,
            "acquire_timeout_seconds": PLUGINS_DB_POOL_ACQUIRE_TIMEOUT,
            "acquire_timeouts_total": timeouts,
            "discards_total": discards,
            "application_name": PLUGINS_DB_APPLICATION_NAME,
        }

    def acquire(
        self, *, timeout_seconds: float = PLUGINS_DB_POOL_ACQUIRE_TIMEOUT
    ) -> Connection[dict[str, Any]]:
        started = time.perf_counter()

        while True:
            try:
                connection = self._available.get_nowait()
                logger.debug(
                    "plugins_pool reuse wait_ms=%.0f",
                    (time.perf_counter() - started) * 1000,
                )
                return connection
            except queue.Empty:
                pass

            with self._lock:
                if self._created < self._max_size:
                    connection = _open_plugins_connection()
                    self._created += 1
                    logger.debug(
                        "plugins_pool created total=%d max=%d wait_ms=%.0f",
                        self._created,
                        self._max_size,
                        (time.perf_counter() - started) * 1000,
                    )
                    return connection

            remaining = timeout_seconds - (time.perf_counter() - started)
            if remaining <= 0:
                with self._lock:
                    self._acquire_timeouts += 1
                logger.warning(
                    "plugins_pool TIMEOUT created=%d max=%d waited=%.0fs",
                    self._created,
                    self._max_size,
                    timeout_seconds,
                )
                raise PluginsDatabaseConnectionError(
                    f"Timeout aguardando conexão no pool de plugins "
                    f"(max={self._max_size})."
                )

            try:
                connection = self._available.get(timeout=min(remaining, 2.0))
                logger.debug(
                    "plugins_pool acquired_after_wait wait_ms=%.0f",
                    (time.perf_counter() - started) * 1000,
                )
                return connection
            except queue.Empty:
                continue

    def release(
        self,
        connection: Connection[dict[str, Any]] | None,
        *,
        discard: bool = False,
    ) -> None:
        if connection is None:
            return

        if discard:
            self._discard(connection)
            return

        try:
            if connection.closed:
                self._discard(connection)
                return
            try:
                connection.rollback()
            except Exception:
                self._discard(connection)
                return
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self._available.put(connection)
        except Exception:
            self._discard(connection)

    def close_all(self) -> None:
        while True:
            try:
                connection = self._available.get_nowait()
            except queue.Empty:
                break
            try:
                if not connection.closed:
                    connection.close()
            except Exception:
                logger.exception("Failed to close pooled plugins connection.")
            with self._lock:
                self._created = max(0, self._created - 1)

    def _discard(self, connection: Connection[dict[str, Any]]) -> None:
        try:
            if not connection.closed:
                connection.close()
        except Exception:
            pass

        with self._lock:
            self._created = max(0, self._created - 1)
            self._discards += 1

        logger.debug("plugins_pool discarded remaining=%d", self._created)


def get_plugins_connection_pool() -> PluginsConnectionPool:
    global _pool
    if _pool is not None:
        return _pool

    with _pool_lock:
        if _pool is None:
            _pool = PluginsConnectionPool(max_size=PLUGINS_DB_POOL_MAX_SIZE)
            logger.info(
                "plugins_pool enabled max_size=%d acquire_timeout=%.1fs",
                PLUGINS_DB_POOL_MAX_SIZE,
                PLUGINS_DB_POOL_ACQUIRE_TIMEOUT,
            )
        return _pool


def reset_plugins_connection_pool_for_tests() -> None:
    """Recria o pool (somente testes)."""
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close_all()
        _pool = None
    _lease_local.stack = []


def _lease_stack() -> list[Connection[dict[str, Any]]]:
    stack = getattr(_lease_local, "stack", None)
    if stack is None:
        stack = []
        _lease_local.stack = stack
    return stack


def current_plugins_lease() -> Connection[dict[str, Any]] | None:
    stack = _lease_stack()
    return stack[-1] if stack else None


def acquire_plugins_connection(
    *, timeout_seconds: float | None = None,
) -> Connection[dict[str, Any]]:
    """
    Obtém conexão do pool.

    Se já houver lease na thread (unidade de trabalho aninhada), reutiliza
    a mesma conexão sem consumir outro slot do pool.
    """
    stack = _lease_stack()
    if stack:
        stack.append(stack[-1])
        return stack[-1]

    timeout = (
        PLUGINS_DB_POOL_ACQUIRE_TIMEOUT
        if timeout_seconds is None
        else timeout_seconds
    )
    connection = get_plugins_connection_pool().acquire(timeout_seconds=timeout)
    stack.append(connection)
    return connection


def release_plugins_connection(
    connection: Connection[dict[str, Any]] | None = None,
    *,
    discard: bool = False,
) -> None:
    """Devolve a conexão ao pool quando o lease mais externo termina."""
    stack = _lease_stack()
    if not stack:
        return

    leased = stack.pop()
    if connection is not None and connection is not leased:
        logger.warning("plugins_pool release mismatch; discarding both handles")
        get_plugins_connection_pool().release(leased, discard=True)
        get_plugins_connection_pool().release(connection, discard=True)
        return

    if stack:
        # Ainda há lease externo na mesma conexão.
        return

    get_plugins_connection_pool().release(leased, discard=discard)


@contextmanager
def plugins_connection(
    *, timeout_seconds: float | None = None,
) -> Iterator[Connection[dict[str, Any]]]:
    connection = acquire_plugins_connection(timeout_seconds=timeout_seconds)
    discard = False
    try:
        yield connection
    except Exception:
        discard = False
        try:
            connection.rollback()
        except Exception:
            discard = True
        raise
    finally:
        release_plugins_connection(connection, discard=discard)


def get_plugins_connection() -> Connection[dict[str, Any]]:
    """
    Compat: adquire (ou reusa lease) do pool.

    Preferir ``plugins_connection()`` / ``acquire``+``release`` em código novo.
    """
    return acquire_plugins_connection()


def close_plugins_connection() -> None:
    """Encerra o pool (shutdown / testes)."""
    global _pool
    _lease_local.stack = []
    with _pool_lock:
        if _pool is not None:
            _pool.close_all()
            _pool = None
    logger.info("Plugins PostgreSQL connection pool closed.")


def check_plugins_connection() -> bool:
    """Executa uma verificação simples de conectividade."""
    try:
        with plugins_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok;")
                row = cursor.fetchone()
            return bool(row and row.get("ok") == 1)
    except Exception:
        logger.exception("Plugins PostgreSQL healthcheck failed.")
        return False
