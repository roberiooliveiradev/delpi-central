"""Regressão: limite de espera no pool TOTVS e isolamento READ UNCOMMITTED.

Incidente 03/11/2026 — backlog ilimitado de requisições esperando conexão
sustentou a saturação mesmo após a demanda cair; e queries a views do ERP
ficaram presas por lock de transação em SB1010 (READ COMMITTED implícito).
"""
from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest

from app.infrastructure.providers.totvs import connection_pool as mod
from app.infrastructure.providers.totvs.connection_pool import (
    create_totvs_connection as _real_create_totvs_connection,
)


@pytest.fixture(autouse=True)
def _reset_totvs_pool(monkeypatch):
    monkeypatch.setattr(mod, "TOTVS_POOL_ENABLED", True)
    monkeypatch.setattr(mod, "TOTVS_POOL_MAX_SIZE", 2)
    monkeypatch.setattr(mod, "TOTVS_POOL_ACQUIRE_TIMEOUT", 5.0)
    monkeypatch.setattr(mod, "TOTVS_POOL_MAX_WAITERS", 1)

    def _fake_create() -> MagicMock:
        conn = MagicMock()
        conn.cursor.return_value = MagicMock()
        return conn

    monkeypatch.setattr(mod, "create_totvs_connection", _fake_create)
    with mod._pool_lock:
        mod._pool = None
    yield
    with mod._pool_lock:
        mod._pool = None


def test_rejects_immediately_when_waiter_quota_full(_reset_totvs_pool):
    pool = mod.get_totvs_connection_pool()
    held_a = pool.acquire(timeout_seconds=1.0)
    held_b = pool.acquire(timeout_seconds=1.0)

    acquired: list = []
    def _waiter() -> None:
        acquired.append(pool.acquire(timeout_seconds=5.0))

    waiter = threading.Thread(target=_waiter, daemon=True)
    waiter.start()
    for _ in range(50):
        if pool.stats()["waiting"] >= 1:
            break
        time.sleep(0.01)
    assert pool.stats()["waiting"] == 1

    started = time.perf_counter()
    with pytest.raises(TimeoutError, match="saturado"):
        pool.acquire(timeout_seconds=30.0)
    assert time.perf_counter() - started < 1.0
    assert pool.stats()["rejected_total"] == 1

    pool.release(held_a)
    waiter.join(timeout=5)
    assert len(acquired) == 1
    pool.release(acquired[0])
    pool.release(held_b)
    assert pool.stats()["waiting"] == 0


def test_create_connection_sets_read_uncommitted(monkeypatch):
    conn = MagicMock()
    monkeypatch.setattr(mod.pyodbc, "connect", MagicMock(return_value=conn))
    monkeypatch.setattr(mod, "build_totvs_connection_string", lambda: "cs")

    result = _real_create_totvs_connection()

    assert result is conn
    conn.execute.assert_called_once_with(
        "SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"
    )
    assert conn.timeout == mod.TOTVS_QUERY_TIMEOUT
