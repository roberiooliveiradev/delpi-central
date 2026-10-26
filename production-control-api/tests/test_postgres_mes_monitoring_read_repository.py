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


def test_live_read_is_consolidated_without_n_plus_1(monkeypatch):
    # 2 queries consolidadas: runs ativos + fatos autônomos (run_id NULL) —
    # PC-MES-CT-AUTONOMOUS-DOWNTIME. Nenhum N+1 por linha.
    cursor = FakeCursor([[{"run_id": "run-1"}], []])
    monkeypatch.setattr(module, "get_connection", lambda: fake_connection(cursor))
    rows = module.PostgresMesMonitoringReadRepository().list_live_work_centers(branch="01")
    assert len(rows) == 1
    assert rows[0]["run_id"] == "run-1"
    assert rows[0]["autonomous_monitoring"] is False
    assert len(cursor.executions) == 2
    sql, params = cursor.executions[0]
    assert "production_runs" in sql
    assert "work_center_state_events" in sql
    assert "downtime_events" in sql
    assert "downtime_reason_catalog" in sql
    assert "status IN ('running', 'paused')" in sql
    assert params == ["01"]
    sql2, params2 = cursor.executions[1]
    assert "run_id IS NULL" in sql2
    assert "work_center_state_events" in sql2
    assert params2 == ["01"]


def test_live_read_includes_autonomous_rows(monkeypatch):
    cursor = FakeCursor([
        [],
        [{"run_id": None, "branch": "01", "work_center": "CT09",
          "operational_state": "stopped", "autonomous_monitoring": True}],
    ])
    monkeypatch.setattr(module, "get_connection", lambda: fake_connection(cursor))
    rows = module.PostgresMesMonitoringReadRepository().list_live_work_centers(branch="01")
    assert len(rows) == 1
    assert rows[0]["run_id"] is None
    assert rows[0]["autonomous_monitoring"] is True


def test_work_center_timeline_is_one_consolidated_overlap_query(monkeypatch):
    cursor = FakeCursor([[{"id": "state-1"}]])
    monkeypatch.setattr(module, "get_connection", lambda: fake_connection(cursor))
    start = datetime(2026, 9, 29, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)
    rows = module.PostgresMesMonitoringReadRepository().list_work_center_timeline_facts(
        branch="01", work_center="CT-35", period_from=start, period_to=end,
    )
    assert rows == [{"id": "state-1"}]
    assert len(cursor.executions) == 1
    sql, params = cursor.executions[0]
    assert "work_center_state_events" in sql
    assert "production_runs" in sql
    assert "downtime_events" in sql
    assert "downtime_reason_catalog" in sql
    assert "s.started_at < %s" in sql
    assert "s.ended_at IS NULL OR s.ended_at >= %s" in sql
    assert params == ["01", "CT-35", end, start]


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


def test_downtime_management_filters_apply_to_count_and_select(monkeypatch):
    cursor = FakeCursor([[{"total": 3}], [{"id": "down-1"}]])
    monkeypatch.setattr(module, "get_connection", lambda: fake_connection(cursor))
    rows, total = module.PostgresMesMonitoringReadRepository().list_downtimes(
        branch="01",
        work_center=None,
        period_from=None,
        period_to=None,
        reason_code="setup",
        source="system",
        classification="pending",
        sort="oldest",
        downtime_id="9f2a1b3c-1234-4abc-9def-000000000001",
        page=1,
        page_size=50,
    )
    assert rows == [{"id": "down-1"}]
    assert total == 3
    assert len(cursor.executions) == 2
    count_sql, count_params = cursor.executions[0]
    select_sql, select_params = cursor.executions[1]
    for sql in (count_sql, select_sql):
        assert "d.reason_code = %s" in sql
        assert "d.source = %s" in sql
        assert "d.confirmed IS NOT TRUE" in sql
        assert "d.id = %s" in sql
    # COUNT usa exatamente os mesmos filtros do SELECT (sem LIMIT/OFFSET).
    assert count_params == [
        "01", "setup", "system", "9f2a1b3c-1234-4abc-9def-000000000001",
    ]
    assert select_params == [
        "01", "setup", "system", "9f2a1b3c-1234-4abc-9def-000000000001", 50, 0,
    ]
    assert "ORDER BY d.started_at ASC, d.id ASC" in select_sql


def test_downtime_confirmed_filter_and_recent_sort(monkeypatch):
    cursor = FakeCursor([[{"total": 1}], [{"id": "down-2"}]])
    monkeypatch.setattr(module, "get_connection", lambda: fake_connection(cursor))
    module.PostgresMesMonitoringReadRepository().list_downtimes(
        branch="01",
        work_center=None,
        period_from=None,
        period_to=None,
        classification="confirmed",
        sort="recent",
        page=1,
        page_size=50,
    )
    select_sql, _ = cursor.executions[1]
    assert "d.confirmed IS TRUE" in select_sql
    assert "ORDER BY d.started_at DESC, d.id DESC" in select_sql
