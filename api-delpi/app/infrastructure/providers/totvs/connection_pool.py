from __future__ import annotations

import logging
import os
import queue
import sys
import threading
import time

import pyodbc

from app.config import settings

logger = logging.getLogger("totvs.pool")
if not logger.handlers:
    _h = logging.StreamHandler(sys.stderr)
    _h.setLevel(logging.WARNING)
    _h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(_h)

TOTVS_CONNECT_TIMEOUT = int(os.getenv("TOTVS_CONNECT_TIMEOUT", "10"))
TOTVS_QUERY_TIMEOUT = int(os.getenv("TOTVS_QUERY_TIMEOUT", "120"))
TOTVS_POOL_ENABLED = os.getenv("TOTVS_POOL_ENABLED", "true").lower() in ("1", "true", "yes")
TOTVS_POOL_MAX_SIZE = int(os.getenv("TOTVS_POOL_MAX_SIZE", "10"))

_pool: TotvsConnectionPool | None = None
_pool_lock = threading.Lock()


def build_totvs_connection_string() -> str:
    host = settings.TOTVS_DB_HOST or settings.DB_HOST
    port = settings.TOTVS_DB_PORT or settings.DB_PORT
    database = settings.TOTVS_DB_DATABASE or settings.DB_DATABASE
    user = settings.TOTVS_DB_USER or settings.DB_USER
    password = settings.TOTVS_DB_PASSWORD or settings.DB_PASSWORD

    if not all([host, database, user, password]):
        raise RuntimeError(
            "Configuração TOTVS incompleta. Defina TOTVS_DB_* ou DB_* no ambiente."
        )

    return (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={host},{port};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={password};"
        "Encrypt=no;"
        "TrustServerCertificate=yes;"
    )


def create_totvs_connection() -> pyodbc.Connection:
    connection = pyodbc.connect(
        build_totvs_connection_string(),
        timeout=TOTVS_CONNECT_TIMEOUT,
    )
    connection.timeout = TOTVS_QUERY_TIMEOUT
    return connection


class TotvsConnectionPool:
    def __init__(self, *, max_size: int) -> None:
        self._max_size = max(1, max_size)
        self._available: queue.Queue[pyodbc.Connection] = queue.Queue()
        self._created = 0
        self._lock = threading.Lock()

    def acquire(self, *, timeout_seconds: float = 60.0) -> pyodbc.Connection:
        started = time.perf_counter()

        while True:
            try:
                connection = self._available.get_nowait()
                logger.debug(
                    "totvs_pool reuse wait_ms=%.0f",
                    (time.perf_counter() - started) * 1000,
                )
                return connection
            except queue.Empty:
                pass

            with self._lock:
                if self._created < self._max_size:
                    connection = create_totvs_connection()
                    self._created += 1
                    logger.debug(
                        "totvs_pool created total=%d max=%d wait_ms=%.0f",
                        self._created,
                        self._max_size,
                        (time.perf_counter() - started) * 1000,
                    )
                    return connection

            remaining = timeout_seconds - (time.perf_counter() - started)
            if remaining <= 0:
                logger.warning(
                    "totvs_pool TIMEOUT created=%d max=%d waited=%.0fs",
                    self._created, self._max_size, timeout_seconds,
                )
                raise TimeoutError(
                    f"Timeout aguardando conexão TOTVS no pool (max={self._max_size})."
                )

            try:
                connection = self._available.get(timeout=min(remaining, 2.0))
                logger.debug(
                    "totvs_pool acquired_after_wait wait_ms=%.0f",
                    (time.perf_counter() - started) * 1000,
                )
                return connection
            except queue.Empty:
                continue

    def release(
        self, connection: pyodbc.Connection | None, *, discard: bool = False,
    ) -> None:
        if connection is None:
            return

        if discard:
            self._discard(connection)
            return

        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            self._available.put(connection)
        except Exception:
            self._discard(connection)

    def _discard(self, connection: pyodbc.Connection) -> None:
        try:
            connection.close()
        except Exception:
            pass

        with self._lock:
            self._created = max(0, self._created - 1)

        logger.debug("totvs_pool discarded remaining=%d", self._created)


def get_totvs_connection_pool() -> TotvsConnectionPool | None:
    if not TOTVS_POOL_ENABLED:
        return None

    global _pool
    if _pool is not None:
        return _pool

    with _pool_lock:
        if _pool is None:
            _pool = TotvsConnectionPool(max_size=TOTVS_POOL_MAX_SIZE)
            logger.info("totvs_pool enabled max_size=%d", TOTVS_POOL_MAX_SIZE)
        return _pool
