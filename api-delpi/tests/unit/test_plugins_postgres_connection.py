"""Regressão: conexão plugins Postgres é por thread (não singleton global)."""
from __future__ import annotations

import threading

from app.infrastructure.providers.database import plugins_postgres_connection as mod


class _FakeConn:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_get_plugins_connection_is_thread_local(monkeypatch):
    created: list[_FakeConn] = []

    def _fake_open() -> _FakeConn:
        conn = _FakeConn()
        created.append(conn)
        return conn  # type: ignore[return-value]

    monkeypatch.setattr(mod, "_open_plugins_connection", _fake_open)
    with mod._registry_lock:
        mod._registered_connections.clear()
    mod._thread_local.connection = None

    main_conn = mod.get_plugins_connection()
    assert mod.get_plugins_connection() is main_conn

    other: list[object] = []

    def _worker() -> None:
        other.append(mod.get_plugins_connection())

    t = threading.Thread(target=_worker)
    t.start()
    t.join(timeout=5)
    assert len(other) == 1
    assert other[0] is not main_conn
    assert len(created) == 2

    mod.close_plugins_connection()
    assert main_conn.closed is True
    assert other[0].closed is True  # type: ignore[union-attr]
