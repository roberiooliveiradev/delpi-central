from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

from production_control_app.infrastructure.persistence import (
    postgres_mes_monitoring_read_repository as module,
)


class FakeCursor:
    def __init__(self, results):
        self.results = list(results)
        self.executions = []
        self.current = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, sql, params):
        self.executions.append((" ".join(sql.split()), list(params)))
        self.current = self.results.pop(0)

    def fetchall(self):
        return self.current

    def fetchone(self):
        return self.current[0]


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def cursor(self):
        return self._cursor


@contextmanager
def fake_connection(cursor):
    yield FakeConnection(cursor)


def test_live_read_is_one_consolidated_query(monkeypatch):
    cursor = FakeCursor([[{"run_id": "run-1"}]])
    monkeypatch.setattr(module, "get_connection", lambda: fake_connection(cursor))
    rows = module.PostgresMesMonitoringReadRepository().list_live_work_centers(branch="01")
    assert rows == [{"run_id": "run-1"}]
    assert len(cursor.executions) == 1
    sql, params = cursor.executions[0]
    assert "production_runs" in sql
    assert "work_center_state_events" in sql
    assert "downtime_events" in sql
    assert "downtime_reason_catalog" in sql
    assert "status IN ('running', 'paused')" in sql
    assert params == ["01"]


def test_downtime_read_is_bounded_and_uses_interval_overlap(monkeypatch):
    cursor = FakeCursor([[{"total": 1}], [{"id": "down-1"}]])
    monkeypatch.setattr(module, "get_connection", lambda: fake_connection(cursor))
    start = datetime(2026, 9, 29, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 9, 29, 11, 0, tzinfo=timezone.utc)
    rows, total = module.PostgresMesMonitoringReadRepository().list_downtimes(
        branch="01",
        work_center="CT-35",
        period_from=start,
        period_to=end,
        page=2,
        page_size=25,
    )
    assert rows == [{"id": "down-1"}]
    assert total == 1
    assert len(cursor.executions) == 2
    sql, params = cursor.executions[1]
    assert "d.started_at < %s" in sql
    assert "d.ended_at IS NULL OR d.ended_at >= %s" in sql
    assert "LIMIT %s OFFSET %s" in sql
    assert params == ["01", "CT-35", end, start, 25, 25]
