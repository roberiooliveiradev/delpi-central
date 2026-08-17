"""Regressão: pool limitado de conexões Postgres plugins (acquire/release)."""
from __future__ import annotations

import threading
import time

import pytest

from app.infrastructure.providers.database import plugins_postgres_connection as mod


class _FakeConn:
    def __init__(self, *, fail_ping: bool = False) -> None:
        self.closed = False
        self._fail_ping = fail_ping
        self.rollback_calls = 0

    def close(self) -> None:
        self.closed = True

    def rollback(self) -> None:
        self.rollback_calls += 1

    def cursor(self):
        return _FakeCursor(self)


class _FakeCursor:
    def __init__(self, conn: _FakeConn) -> None:
        self._conn = conn

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, *args) -> None:
        return None

    def execute(self, query: str, params=None) -> None:
        if self._conn._fail_ping and "SELECT 1" in query:
            raise RuntimeError("ping failed")


@pytest.fixture(autouse=True)
def _reset_pool(monkeypatch):
    created: list[_FakeConn] = []

    def _fake_open() -> _FakeConn:
        conn = _FakeConn()
        created.append(conn)
        return conn  # type: ignore[return-value]

    monkeypatch.setattr(mod, "_open_plugins_connection", _fake_open)
    monkeypatch.setattr(mod, "PLUGINS_DB_POOL_MAX_SIZE", 2)
    monkeypatch.setattr(mod, "PLUGINS_DB_POOL_ACQUIRE_TIMEOUT", 0.2)
    mod.reset_plugins_connection_pool_for_tests()
    yield created
    mod.reset_plugins_connection_pool_for_tests()


def test_pool_reuses_released_connection(_reset_pool):
    created = _reset_pool
    first = mod.acquire_plugins_connection()
    mod.release_plugins_connection(first)
    second = mod.acquire_plugins_connection()
    mod.release_plugins_connection(second)
    assert first is second
    assert len(created) == 1


def test_pool_respects_max_size(_reset_pool):
    created = _reset_pool
    barrier = threading.Barrier(2)
    release_gate = threading.Event()

    def _hold() -> None:
        conn = mod.acquire_plugins_connection(timeout_seconds=1.0)
        barrier.wait(timeout=2)
        release_gate.wait(timeout=2)
        mod.release_plugins_connection(conn)

    t1 = threading.Thread(target=_hold)
    t2 = threading.Thread(target=_hold)
    t1.start()
    t2.start()
    # Both threads reached barrier ⇒ 2 connections created and held.
    time.sleep(0.05)
    # Wait until barrier is waiting (both acquired)
    deadline = time.time() + 2
    while time.time() < deadline and len(created) < 2:
        time.sleep(0.01)
    assert len(created) == 2

    def _timeout_acquire() -> None:
        with pytest.raises(mod.PluginsDatabaseConnectionError):
            mod.acquire_plugins_connection(timeout_seconds=0.15)

    t3 = threading.Thread(target=_timeout_acquire)
    t3.start()
    t3.join(timeout=2)
    assert not t3.is_alive()

    release_gate.set()
    t1.join(timeout=2)
    t2.join(timeout=2)


def test_nested_lease_reuses_same_connection(_reset_pool):
    created = _reset_pool
    outer = mod.acquire_plugins_connection()
    inner = mod.acquire_plugins_connection()
    assert outer is inner
    assert len(created) == 1
    mod.release_plugins_connection(inner)
    mod.release_plugins_connection(outer)
    assert len(created) == 1


def test_plugins_connection_context_manager_releases(_reset_pool):
    created = _reset_pool
    with mod.plugins_connection() as conn:
        assert conn is not None
    assert len(created) == 1
    again = mod.acquire_plugins_connection()
    assert again is created[0]
    mod.release_plugins_connection(again)


def test_release_discards_dead_connection(monkeypatch, _reset_pool):
    created = _reset_pool

    def _open_bad() -> _FakeConn:
        conn = _FakeConn(fail_ping=True)
        created.append(conn)
        return conn  # type: ignore[return-value]

    monkeypatch.setattr(mod, "_open_plugins_connection", _open_bad)
    mod.reset_plugins_connection_pool_for_tests()

    conn = mod.acquire_plugins_connection()
    mod.release_plugins_connection(conn, discard=False)
    assert conn.closed is True
    assert mod.get_plugins_connection_pool().created == 0


def test_close_plugins_connection_drains_pool(_reset_pool):
    created = _reset_pool
    a = mod.acquire_plugins_connection()
    mod.release_plugins_connection(a)
    mod.close_plugins_connection()
    assert created[0].closed is True
    assert mod._pool is None


def test_concurrent_acquire_does_not_exceed_max(_reset_pool):
    created = _reset_pool
    barrier = threading.Barrier(4)
    held: list[object] = []
    lock = threading.Lock()

    def _worker() -> None:
        barrier.wait(timeout=2)
        conn = mod.acquire_plugins_connection(timeout_seconds=2.0)
        with lock:
            held.append(conn)
        time.sleep(0.05)
        mod.release_plugins_connection(conn)

    threads = [threading.Thread(target=_worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5)
    assert all(not t.is_alive() for t in threads)
    assert len(created) <= 2
