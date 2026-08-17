"""Regressão: stats() do TotvsConnectionPool."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.infrastructure.providers.totvs import connection_pool as mod


@pytest.fixture(autouse=True)
def _reset_totvs_pool(monkeypatch):
    monkeypatch.setattr(mod, "TOTVS_POOL_ENABLED", True)
    monkeypatch.setattr(mod, "TOTVS_POOL_MAX_SIZE", 2)
    monkeypatch.setattr(mod, "TOTVS_POOL_ACQUIRE_TIMEOUT", 0.2)

    def _fake_create() -> MagicMock:
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value = cursor
        return conn

    monkeypatch.setattr(mod, "create_totvs_connection", _fake_create)
    with mod._pool_lock:
        mod._pool = None
    yield
    with mod._pool_lock:
        mod._pool = None


def test_totvs_pool_stats_and_timeout_counter(_reset_totvs_pool):
    pool = mod.get_totvs_connection_pool()
    assert pool is not None
    stats0 = pool.stats()
    assert stats0["enabled"] is True
    assert stats0["max_size"] == 2
    assert stats0["in_use"] == 0

    a = pool.acquire(timeout_seconds=1.0)
    b = pool.acquire(timeout_seconds=1.0)
    busy = pool.stats()
    assert busy["created"] == 2
    assert busy["in_use"] == 2
    assert busy["available"] == 0

    with pytest.raises(TimeoutError):
        pool.acquire(timeout_seconds=0.05)
    assert pool.stats()["acquire_timeouts_total"] >= 1

    pool.release(a)
    pool.release(b)
    idle = pool.stats()
    assert idle["available"] == 2
    assert idle["in_use"] == 0


def test_totvs_pool_discard_increments_counter(_reset_totvs_pool):
    pool = mod.get_totvs_connection_pool()
    assert pool is not None
    conn = pool.acquire(timeout_seconds=1.0)
    pool.release(conn, discard=True)
    assert pool.stats()["discards_total"] >= 1
    assert pool.stats()["created"] == 0
