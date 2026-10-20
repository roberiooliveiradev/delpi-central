"""Regression: SettlementsRepository must acquire/release the TOTVS
connection through the BaseRepository context manager.

Before the fix, public methods called ``execute_*`` directly with
``self.cursor is None``, producing ``'NoneType' object has no attribute
'execute'`` (HTTP 500) on the first real call — invisible to tests that
mock the repository itself.
"""

from __future__ import annotations

from app.infrastructure.persistence.totvs import base_repository
from app.infrastructure.persistence.totvs.financeiro_settlements.settlements_repository import (
    SettlementsRepository,
)


class _FakeCursor:
    def __init__(self) -> None:
        self.executed: list[tuple[str, object]] = []
        self.description = [("total_items",)]
        self.closed = False

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def fetchone(self):
        return (7,)

    def fetchall(self):
        return [(7,)]

    def close(self):
        self.closed = True


class _FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = _FakeCursor()

    def cursor(self):
        return self.cursor_instance


def _patch_pool(monkeypatch):
    conn = _FakeConnection()
    released: list[tuple[object, bool]] = []
    monkeypatch.setattr(base_repository, "get_connection", lambda: conn)
    monkeypatch.setattr(
        base_repository,
        "release_connection",
        lambda c, *, discard=False: released.append((c, discard)),
    )
    return conn, released


def test_count_settlements_acquires_and_releases_connection(monkeypatch):
    conn, released = _patch_pool(monkeypatch)

    total = SettlementsRepository().count_settlements(
        side="payable", start_date="2026-10-01", end_date="2026-10-20"
    )

    assert total == 7
    assert conn.cursor_instance.executed, "query never reached a real cursor"
    assert released == [(conn, False)]


def test_summary_groups_acquires_and_releases_connection(monkeypatch):
    conn, released = _patch_pool(monkeypatch)

    rows = SettlementsRepository().summary_groups(
        start_date="2026-10-01", end_date="2026-10-20"
    )

    assert rows == [{"total_items": 7}]
    assert conn.cursor_instance.executed
    assert released == [(conn, False)]
