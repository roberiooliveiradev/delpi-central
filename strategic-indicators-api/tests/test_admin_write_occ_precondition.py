"""W013-ACT — owner-side atomic OCC for admin department/indicator/CR writes.

Verifies with an injected fake connection that:

- department/indicator UPDATE reads the row FOR UPDATE and compares the
  sealed ``expected_row_xmin`` inside the same transaction (atomic
  precondition covering the multi-statement rename path);
- activate/deactivate evaluate ``expected_xmin`` in the same atomic
  UPDATE statement;
- stale tokens raise StrategicIndicatorsAdminConflictError;
- CR submit guards on ``status = 'draft'`` + ``xmin`` atomically and is
  idempotent on replay;
- CR create/comment honour the idempotency key via ON CONFLICT.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pytest

from si_app.application.services.strategic_indicators.admin_write_conflict_error import (
    StrategicIndicatorsAdminConflictError,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_admin_departments_repository import (
    PostgresStrategicIndicatorsAdminDepartmentsRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_department_indicators_repository import (
    PostgresStrategicIndicatorsDepartmentIndicatorsRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_change_request_repository import (
    PostgresStrategicIndicatorsChangeRequestRepository,
)


class _FakeCursor:
    def __init__(self, conn: "_FakeConnection") -> None:
        self._conn = conn
        self._row: dict | None = None

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    def execute(self, query: str, params: tuple = ()) -> None:
        self._conn.statements.append((query, params))
        self._row = self._conn.next_row

    def fetchone(self) -> dict | None:
        override = getattr(self._conn, "fetch_override", None)
        if override is not None:
            return override()
        return self._row

    def fetchall(self) -> list:
        return self._conn.next_rows


class _FakeConnection:
    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple]] = []
        self.next_row: dict | None = None
        self.next_rows: list = []
        self.commits = 0
        self.rollbacks = 0

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


_DEPT_ROW = {
    "department_id": "fin",
    "department_name": "Fin",
    "short_name": "FIN",
    "strategic_summary": "s",
    "headline_goal": "h",
    "supporting_focus": "f",
    "weight_pct": 30.0,
    "aggregation_mode": "consolidated",
    "is_active": True,
    "display_order": 1,
    "row_xmin": "100",
}


def _queued_fetch(rows: list[dict | None]):
    """Return a fetch_override that pops one queued row per statement."""
    queue = list(rows)

    def _next() -> dict | None:
        return queue.pop(0) if queue else None

    return _next


# ------------------------------------------------------------- departments
def test_dept_update_locks_row_and_compares_xmin() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch([dict(_DEPT_ROW), dict(_DEPT_ROW)])
    repo = PostgresStrategicIndicatorsAdminDepartmentsRepository(connection=conn)
    repo.update_department(
        department_id="fin",
        new_department_id=None,
        department_name="Fin",
        short_name="FIN",
        strategic_summary="s",
        headline_goal="h",
        supporting_focus="f",
        weight_pct=40.0,
        aggregation_mode="consolidated",
        is_active=True,
        display_order=1,
        actor_user_id="u-1",
        expected_row_xmin="100",
    )
    lock_sql = [s for s, _ in conn.statements if "FOR UPDATE" in s]
    assert len(lock_sql) == 1
    assert "xmin::text AS row_xmin" in lock_sql[0]
    # Guarded read → compare → UPDATE share one transaction (no commits
    # inside the unit of work with an injected connection).
    assert conn.commits == 0


def test_dept_update_stale_xmin_raises_conflict() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch([dict(_DEPT_ROW)])
    repo = PostgresStrategicIndicatorsAdminDepartmentsRepository(connection=conn)
    with pytest.raises(StrategicIndicatorsAdminConflictError):
        repo.update_department(
            department_id="fin",
            new_department_id=None,
            department_name="Fin",
            short_name="FIN",
            strategic_summary="s",
            headline_goal="h",
            supporting_focus="f",
            weight_pct=40.0,
            aggregation_mode="consolidated",
            is_active=True,
            display_order=1,
            actor_user_id="u-1",
            expected_row_xmin="STALE",
        )
    updates = [s for s, _ in conn.statements if "UPDATE strategic_indicators.departments" in s]
    assert updates == []  # refused before mutating


def test_dept_activate_atomic_xmin_predicate() -> None:
    conn = _FakeConnection()
    conn.next_row = dict(_DEPT_ROW)
    repo = PostgresStrategicIndicatorsAdminDepartmentsRepository(connection=conn)
    repo.activate_department(
        department_id="fin", actor_user_id="u-1", expected_xmin="100"
    )
    guarded = [s for s, _ in conn.statements if "xmin::text = %s" in s]
    assert len(guarded) == 1
    assert "%s::text IS NULL OR xmin::text = %s" in guarded[0]


def test_dept_activate_stale_xmin_raises_conflict() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch([dict(_DEPT_ROW), None])
    repo = PostgresStrategicIndicatorsAdminDepartmentsRepository(connection=conn)
    with pytest.raises(StrategicIndicatorsAdminConflictError):
        repo.activate_department(
            department_id="fin", actor_user_id="u-1", expected_xmin="STALE"
        )


def test_dept_create_conflict_and_audit_event() -> None:
    conn = _FakeConnection()
    # pre-check finds existing row → conflict, no INSERT issued
    conn.next_row = {"department_id": "fin"}
    repo = PostgresStrategicIndicatorsAdminDepartmentsRepository(connection=conn)
    with pytest.raises(StrategicIndicatorsAdminConflictError):
        repo.create_department(
            department_id="fin",
            department_name="Fin",
            short_name="FIN",
            strategic_summary="s",
            headline_goal="h",
            supporting_focus="f",
            weight_pct=10.0,
            aggregation_mode="consolidated",
            display_order=1,
            actor_user_id="u-1",
        )
    inserts = [s for s, _ in conn.statements if "INSERT INTO strategic_indicators.departments" in s]
    assert inserts == []


def test_dept_create_insert_is_atomic_on_conflict() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch([None, dict(_DEPT_ROW), None])
    repo = PostgresStrategicIndicatorsAdminDepartmentsRepository(connection=conn)
    repo.create_department(
        department_id="fin",
        department_name="Fin",
        short_name="FIN",
        strategic_summary="s",
        headline_goal="h",
        supporting_focus="f",
        weight_pct=10.0,
        aggregation_mode="consolidated",
        display_order=1,
        actor_user_id="u-1",
        audit_origin="davi-mcp",
        correlation_id="prop-1",
    )
    inserts = [
        s
        for s, _ in conn.statements
        if "INSERT INTO strategic_indicators.departments" in s
    ]
    assert len(inserts) == 1
    assert "ON CONFLICT (department_id) DO NOTHING" in inserts[0]
    audits = [
        s
        for s, _ in conn.statements
        if "strategic_indicators.settings_audit" in s
    ]
    assert audits, "audit event must ride the same transaction"


# ------------------------------------------------------------- indicators
def test_indicator_update_locks_row_and_compares_xmin() -> None:
    conn = _FakeConnection()
    ind = {"indicator_id": "i-1", "department_id": "fin", "row_xmin": "110"}
    conn.fetch_override = _queued_fetch([dict(ind), dict(ind)])
    repo = PostgresStrategicIndicatorsDepartmentIndicatorsRepository(
        connection=conn
    )
    repo.update_department_indicator(
        indicator_id="i-1",
        new_indicator_id=None,
        indicator_name="I",
        weight_pct=50.0,
        scope_type="consolidated",
        performance_direction="higher_is_better",
        strategic_description="d",
        source_key=None,
        value_unit=None,
        value_prefix=None,
        value_suffix=None,
        value_decimals=2,
        branch_value_aggregation="auto",
        is_active=True,
        display_order=1,
        actor_user_id="u-1",
        expected_row_xmin="110",
    )
    lock_sql = [s for s, _ in conn.statements if "FOR UPDATE" in s]
    assert len(lock_sql) == 1


def test_indicator_toggle_atomic_xmin_predicate() -> None:
    conn = _FakeConnection()
    conn.next_row = {"indicator_id": "i-1", "row_xmin": "110"}
    repo = PostgresStrategicIndicatorsDepartmentIndicatorsRepository(
        connection=conn
    )
    repo.deactivate_department_indicator(
        indicator_id="i-1", actor_user_id="u-1", expected_xmin="110"
    )
    guarded = [s for s, _ in conn.statements if "xmin::text = %s" in s]
    assert len(guarded) == 1


# ------------------------------------------------------------- change requests
def test_cr_submit_guards_status_and_xmin_atomically() -> None:
    conn = _FakeConnection()
    conn.next_row = {"id": "cr-1", "status": "draft", "row_xmin": "120"}
    repo = PostgresStrategicIndicatorsChangeRequestRepository(connection=conn)
    repo.submit_change_request(
        change_request_id="cr-1", actor_user_id="u-1", expected_xmin="120"
    )
    updates = [
        s
        for s, _ in conn.statements
        if "UPDATE strategic_indicators.settings_change_requests" in s
    ]
    assert len(updates) == 1
    assert "status = 'draft'" in updates[0]
    assert "%s::text IS NULL OR xmin::text = %s" in updates[0]


def test_cr_submit_already_submitted_is_idempotent() -> None:
    conn = _FakeConnection()
    submitted = {"id": "cr-1", "status": "submitted", "row_xmin": "121"}
    conn.fetch_override = _queued_fetch([dict(submitted), None, dict(submitted)])
    repo = PostgresStrategicIndicatorsChangeRequestRepository(connection=conn)
    row = repo.submit_change_request(
        change_request_id="cr-1", actor_user_id="u-1", expected_xmin="121"
    )
    assert row["status"] == "submitted"


def test_cr_create_uses_on_conflict_idempotency() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch([None, {"id": "cr-9", "status": "draft"}])
    repo = PostgresStrategicIndicatorsChangeRequestRepository(connection=conn)
    repo.create_change_request(
        title="t",
        description="d",
        target_block="departments",
        proposed_payload={"a": 1},
        actor_user_id="u-1",
        idempotency_key="prop-1",
    )
    inserts = [
        s
        for s, _ in conn.statements
        if "INSERT INTO strategic_indicators.settings_change_requests" in s
    ]
    assert len(inserts) == 1
    assert "ON CONFLICT (idempotency_key)" in inserts[0]


def test_cr_create_replay_returns_existing() -> None:
    conn = _FakeConnection()
    existing = {"id": "cr-1", "status": "draft", "row_xmin": "120"}
    conn.fetch_override = _queued_fetch([{"id": "cr-1"}, dict(existing)])
    repo = PostgresStrategicIndicatorsChangeRequestRepository(connection=conn)
    row = repo.create_change_request(
        title="t",
        description="d",
        target_block="departments",
        proposed_payload={},
        actor_user_id="u-1",
        idempotency_key="prop-1",
    )
    assert row["id"] == "cr-1"
    inserts = [
        s
        for s, _ in conn.statements
        if "INSERT INTO strategic_indicators.settings_change_requests" in s
    ]
    assert inserts == []
