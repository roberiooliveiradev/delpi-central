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

POOL_MAX_SIZE = int(os.getenv("PLUGINS_DB_POOL_MAX_SIZE", "5") or "5")
POOL_ACQUIRE_TIMEOUT = float(
    os.getenv("PLUGINS_DB_POOL_ACQUIRE_TIMEOUT", "30") or "30"
)
APPLICATION_NAME = (
    os.getenv("PLUGINS_DB_APPLICATION_NAME", "bpmn-modeler-api").strip()
    or "bpmn-modeler-api"
)
STATEMENT_TIMEOUT_MS = int(os.getenv("PLUGINS_DB_STATEMENT_TIMEOUT_MS", "30000") or "30000")

_pool: BpmnModelerConnectionPool | None = None
_pool_lock = threading.Lock()
_lease_local = threading.local()


class DatabaseConfigError(RuntimeError):
    pass


class DatabaseConnectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class DbSettings:
    host: str
    port: int
    database: str
    user: str
    password: str
    connect_timeout: int = 5
    sslmode: str = "prefer"
    application_name: str = "bpmn-modeler-api"

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
            f"application_name={self.application_name} "
            f"options='-c statement_timeout={STATEMENT_TIMEOUT_MS}'"
        )


def _read_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise DatabaseConfigError(f"Required environment variable missing: {name}")
    return value


def get_db_settings() -> DbSettings:
    """Shared plugins_hub database — platform convention (PLUGINS_DB_*)."""
    try:
        port = int(_read_required_env("PLUGINS_DB_PORT"))
    except ValueError as exc:
        raise DatabaseConfigError("PLUGINS_DB_PORT must be an integer.") from exc
    return DbSettings(
        host=_read_required_env("PLUGINS_DB_HOST"),
        port=port,
        database=_read_required_env("PLUGINS_DB_NAME"),
        user=_read_required_env("PLUGINS_DB_USER"),
        password=_read_required_env("PLUGINS_DB_PASSWORD"),
        connect_timeout=int(os.getenv("PLUGINS_DB_CONNECT_TIMEOUT", "5")),
        sslmode=os.getenv("PLUGINS_DB_SSLMODE", "prefer").strip() or "prefer",
        application_name=APPLICATION_NAME,
    )


def _open_connection() -> Connection[dict[str, Any]]:
    settings = get_db_settings()
    try:
        return psycopg.connect(
            conninfo=settings.dsn, row_factory=dict_row, autocommit=False
        )
    except Exception as exc:
        logger.exception("Failed to connect to plugins_hub database.")
        raise DatabaseConnectionError(
            "Could not connect to the plugins_hub database."
        ) from exc


class BpmnModelerConnectionPool:
    def __init__(self, *, max_size: int) -> None:
        self._max_size = max(1, max_size)
        self._available: queue.Queue[Connection[dict[str, Any]]] = queue.Queue()
        self._created = 0
        self._lock = threading.Lock()

    def acquire(
        self, *, timeout_seconds: float = POOL_ACQUIRE_TIMEOUT
    ) -> Connection[dict[str, Any]]:
        started = time.perf_counter()
        while True:
            try:
                return self._available.get_nowait()
            except queue.Empty:
                pass
            with self._lock:
                if self._created < self._max_size:
                    connection = _open_connection()
                    self._created += 1
                    return connection
            remaining = timeout_seconds - (time.perf_counter() - started)
            if remaining <= 0:
                raise DatabaseConnectionError("Connection pool acquire timeout.")
            try:
                return self._available.get(timeout=min(remaining, 2.0))
            except queue.Empty:
                continue

    def release(
        self, connection: Connection[dict[str, Any]] | None, *, discard: bool = False
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
                logger.exception("Failed to close pooled connection.")
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


def get_pool() -> BpmnModelerConnectionPool:
    global _pool
    if _pool is not None:
        return _pool
    with _pool_lock:
        if _pool is None:
            _pool = BpmnModelerConnectionPool(max_size=POOL_MAX_SIZE)
        return _pool


def reset_pool_for_tests() -> None:
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


def acquire_connection(
    *, timeout_seconds: float | None = None
) -> Connection[dict[str, Any]]:
    stack = _lease_stack()
    if stack:
        stack.append(stack[-1])
        return stack[-1]
    connection = get_pool().acquire(
        timeout_seconds=POOL_ACQUIRE_TIMEOUT
        if timeout_seconds is None
        else timeout_seconds
    )
    stack.append(connection)
    return connection


def release_connection(
    connection: Connection[dict[str, Any]] | None = None, *, discard: bool = False
) -> None:
    stack = _lease_stack()
    if not stack:
        return
    leased = stack.pop()
    if connection is not None and connection is not leased:
        get_pool().release(leased, discard=True)
        get_pool().release(connection, discard=True)
        return
    if stack:
        return
    get_pool().release(leased, discard=discard)


@contextmanager
def db_connection(
    *, timeout_seconds: float | None = None
) -> Iterator[Connection[dict[str, Any]]]:
    connection = acquire_connection(timeout_seconds=timeout_seconds)
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
        release_connection(connection, discard=discard)


def check_connection() -> bool:
    try:
        with db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok;")
                row = cursor.fetchone()
            return bool(row and row.get("ok") == 1)
    except Exception:
        logger.exception("bpmn_modeler database healthcheck failed.")
        return False
