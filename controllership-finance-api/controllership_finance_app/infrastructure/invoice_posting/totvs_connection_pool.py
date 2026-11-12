from __future__ import annotations

import logging
import os
import queue
import sys
import threading
import time

import pyodbc

from controllership_finance_app.config import settings

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
TOTVS_POOL_ACQUIRE_TIMEOUT = float(os.getenv("TOTVS_POOL_ACQUIRE_TIMEOUT", "60") or "60")
TOTVS_POOL_MAX_WAITERS = int(os.getenv("TOTVS_POOL_MAX_WAITERS", "30") or "30")

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
    # Leitura TOTVS segue a convenção NOLOCK já usada nas queries do codebase.
    # Em nível de sessão, cobre também objetos internos de views do ERP que
    # leem sem hint — evita que uma transação bloqueante no ERP (ex.: lock em
    # SB1010, observado em 03/11/2026) segure conexões do pool até o timeout.
    connection.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED")
    return connection


class TotvsConnectionPool:
    def __init__(self, *, max_size: int) -> None:
        self._max_size = max(1, max_size)
        self._available: queue.Queue[pyodbc.Connection] = queue.Queue()
        self._created = 0
        self._acquire_timeouts = 0
        self._discards = 0
        self._waiting = 0
        self._rejected = 0
        self._lock = threading.Lock()

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def created(self) -> int:
        with self._lock:
            return self._created

    def stats(self) -> dict:
        with self._lock:
            created = self._created
            timeouts = self._acquire_timeouts
            discards = self._discards
            waiting = self._waiting
            rejected = self._rejected
        available = self._available.qsize()
        in_use = max(0, created - available)
        return {
            "enabled": True,
            "max_size": self._max_size,
            "created": created,
            "available": available,
            "in_use": in_use,
            "waiting": waiting,
            "max_waiters": TOTVS_POOL_MAX_WAITERS,
            "acquire_timeout_seconds": TOTVS_POOL_ACQUIRE_TIMEOUT,
            "acquire_timeouts_total": timeouts,
            "rejected_total": rejected,
            "discards_total": discards,
        }

    def acquire(
        self, *, timeout_seconds: float = TOTVS_POOL_ACQUIRE_TIMEOUT,
    ) -> pyodbc.Connection:
        started = time.perf_counter()

        try:
            connection = self._available.get_nowait()
            logger.debug("totvs_pool reuse wait_ms=0")
            return connection
        except queue.Empty:
            pass

        with self._lock:
            if self._created < self._max_size:
                # Reserva a vaga sob lock e cria FORA dele: pyodbc.connect pode
                # levar segundos e bloquearia acquire/release de todo o pool.
                self._created += 1
                reserved = True
            elif self._waiting >= TOTVS_POOL_MAX_WAITERS:
                self._rejected += 1
                reserved = False
                reject = True
            else:
                self._waiting += 1
                reserved = False
                reject = False

        if reserved:
            try:
                connection = create_totvs_connection()
            except Exception:
                with self._lock:
                    self._created = max(0, self._created - 1)
                raise
            logger.debug(
                "totvs_pool created total=%d max=%d wait_ms=%.0f",
                self._created,
                self._max_size,
                (time.perf_counter() - started) * 1000,
            )
            return connection

        if reject:
            # Sem cota de espera ilimitada: requisições enfileiradas por 60s+
            # seguravam worker threads e transformavam um pico transitório em
            # saturação sustentada (backlog interno do api-delpi em 03/11/2026).
            logger.warning(
                "totvs_pool REJECTED created=%d max=%d waiting>=%d",
                self._created, self._max_size, TOTVS_POOL_MAX_WAITERS,
            )
            raise TimeoutError(
                f"Pool TOTVS saturado (esperando>={TOTVS_POOL_MAX_WAITERS})."
            )

        try:
            while True:
                try:
                    connection = self._available.get_nowait()
                    logger.debug(
                        "totvs_pool acquired_after_wait wait_ms=%.0f",
                        (time.perf_counter() - started) * 1000,
                    )
                    return connection
                except queue.Empty:
                    pass

                with self._lock:
                    if self._created < self._max_size:
                        self._created += 1
                        create_outside = True
                    else:
                        create_outside = False

                if create_outside:
                    try:
                        connection = create_totvs_connection()
                    except Exception:
                        with self._lock:
                            self._created = max(0, self._created - 1)
                        raise
                    return connection

                remaining = timeout_seconds - (time.perf_counter() - started)
                if remaining <= 0:
                    with self._lock:
                        self._acquire_timeouts += 1
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
        finally:
            with self._lock:
                self._waiting -= 1

    def release(
        self, connection: pyodbc.Connection | None, *, discard: bool = False,
    ) -> None:
        if connection is None:
            return

        if discard:
            self._discard(connection)
            return

        try:
            # Transação implícita pendente (autocommit off no pyodbc) não pode
            # viajar com a conexão para o próximo locatário.
            connection.rollback()
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
            self._discards += 1

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
