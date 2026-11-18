"""W015 — owner-side atomic OCC + dependent guards for destructive deletes.

Verifies with an injected fake connection that:

- goal delete is a single transaction: scope lock → guarded DELETE with an
  in-statement ``xmin`` precondition → audit event with cascade counts and
  ``_audit_meta`` provenance riding ``payload_before``;
- indicator delete locks the row FOR UPDATE, re-checks ``expected_xmin``
  inside the transaction, enforces ``expected_goal_count`` against the
  locked dependent set, cascades goals+targets and audits the totals;
- department delete locks the department AND its indicator rows FOR
  UPDATE, enforces ``expected_indicator_count``/``expected_goal_count``
  and audits the full cascade;
- stale ``expected_xmin``/count mismatches raise the typed conflict
  BEFORE any mutation statement executes.
"""

from __future__ import annotations

import pytest

from si_app.application.services.strategic_indicators.admin_write_conflict_error import (
    StrategicIndicatorsAdminConflictError,
)
from si_app.application.services.strategic_indicators.indicator_goal_conflict_error import (
    StrategicIndicatorsGoalConflictError,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_admin_departments_repository import (
    PostgresStrategicIndicatorsAdminDepartmentsRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_department_indicators_repository import (
    PostgresStrategicIndicatorsDepartmentIndicatorsRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
    PostgresStrategicIndicatorsIndicatorGoalsRepository,
)


class _FakeCursor:
    def __init__(self, conn: "_FakeConnection") -> None:
        self._conn = conn
        self._row: dict | None = None

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *exc) -> bool:
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


def _queued_fetch(rows: list[dict | None]):
    queue = list(rows)

    def _next() -> dict | None:
        return queue.pop(0) if queue else None

    return _next


_GOAL_ROW = {
    "id": "g-1",
    "indicator_id": "ind-1",
    "goal_year": 2025,
    "goal_scope_branch": "",
    "version": 1,
    "is_active": True,
    "row_xmin": "1001",
}
_IND_ROW = {
    "indicator_id": "ind-1",
    "department_id": "fin",
    "indicator_name": "Margem",
    "is_active": True,
    "row_xmin": "3001",
}
_DEPT_ROW = {
    "department_id": "fin",
    "department_name": "Fin",
    "is_active": True,
    "row_xmin": "2001",
}


# ------------------------------------------------------------------- goals


def test_goal_delete_atomic_xmin_guard_and_audit() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch(
        [
            dict(_GOAL_ROW),       # before_row
            {"cnt": 12},           # monthly targets
            {"cnt": 1},            # copied_from refs
            dict(_GOAL_ROW),       # DELETE ... RETURNING *
        ]
    )
    repo = PostgresStrategicIndicatorsIndicatorGoalsRepository(connection=conn)
    result = repo.delete_indicator_goal(
        goal_id="g-1",
        actor_user_id="u-1",
        expected_xmin="1001",
        audit_origin="davi-mcp",
        correlation_id="p-1",
    )
    assert result["goal_id"] == "g-1"

    guarded = [
        s for s, _ in conn.statements
        if "DELETE FROM strategic_indicators.indicator_goals" in s
        and "xmin::text = %s" in s
    ]
    assert len(guarded) == 1
    assert "pg_advisory_xact_lock" in "\n".join(s for s, _ in conn.statements)
    audit = [
        s for s, _ in conn.statements
        if "INSERT INTO strategic_indicators.settings_audit" in s
    ]
    assert len(audit) == 1
    params = [p for s, p in conn.statements if s == audit[0]][0]
    payload_before = str(params)
    assert "_audit_meta" in payload_before
    assert "davi-mcp" in payload_before
    assert "monthly_targets_deleted" in payload_before


def test_goal_delete_stale_xmin_raises_conflict_no_audit() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch(
        [
            dict(_GOAL_ROW),  # before_row
            {"cnt": 0},
            {"cnt": 0},
            None,             # guarded DELETE returns nothing → stale
        ]
    )
    repo = PostgresStrategicIndicatorsIndicatorGoalsRepository(connection=conn)
    with pytest.raises(StrategicIndicatorsGoalConflictError):
        repo.delete_indicator_goal(
            goal_id="g-1",
            actor_user_id="u-1",
            expected_xmin="STALE",
        )
    audit = [
        s for s, _ in conn.statements
        if "INSERT INTO strategic_indicators.settings_audit" in s
    ]
    assert audit == []


def test_goal_delete_missing_raises_not_found() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch([None])
    repo = PostgresStrategicIndicatorsIndicatorGoalsRepository(connection=conn)
    with pytest.raises(ValueError):
        repo.delete_indicator_goal(goal_id="g-none", actor_user_id="u-1")


# --------------------------------------------------------------- indicators


def test_indicator_delete_locks_row_and_guards_counts() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch(
        [
            dict(_IND_ROW),             # FOR UPDATE row
            {"row_xmin": "3001"},       # xmin re-read
            {"cnt": 2},                 # goals count == expected
            {"cnt": 24},                # monthly count
            dict(_IND_ROW),             # DELETE RETURNING
        ]
    )
    repo = PostgresStrategicIndicatorsDepartmentIndicatorsRepository(connection=conn)
    result = repo.delete_department_indicator(
        indicator_id="ind-1",
        actor_user_id="u-1",
        expected_xmin="3001",
        expected_goal_count=2,
    )
    assert result["indicator_id"] == "ind-1"
    first = conn.statements[0][0]
    assert "FOR UPDATE" in first
    cascade = [
        s for s, _ in conn.statements
        if "DELETE FROM strategic_indicators.indicator_goals" in s
    ]
    assert cascade  # dependent goals wiped in-tx
    audit = [
        p for s, p in conn.statements
        if "INSERT INTO strategic_indicators.settings_audit" in s
    ]
    assert audit and "_audit_meta" in str(audit[0])
    assert "indicator_goals_deleted" in str(audit[0])


def test_indicator_delete_stale_xmin_conflict_before_mutation() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch(
        [dict(_IND_ROW), {"row_xmin": "DIFFERENT"}]
    )
    repo = PostgresStrategicIndicatorsDepartmentIndicatorsRepository(connection=conn)
    with pytest.raises(StrategicIndicatorsAdminConflictError):
        repo.delete_department_indicator(
            indicator_id="ind-1",
            actor_user_id="u-1",
            expected_xmin="3001",
        )
    deletes = [
        s for s, _ in conn.statements if "DELETE FROM" in s
    ]
    assert deletes == []


def test_indicator_delete_goal_count_mismatch_conflict() -> None:
    conn = _FakeConnection()
    conn.fetch_override = _queued_fetch(
        [
            dict(_IND_ROW),
            {"row_xmin": "3001"},
            {"cnt": 3},  # locked set has 3, expected 2 → conflict
        ]
    )
    repo = PostgresStrategicIndicatorsDepartmentIndicatorsRepository(connection=conn)
    with pytest.raises(StrategicIndicatorsAdminConflictError):
        repo.delete_department_indicator(
            indicator_id="ind-1",
            actor_user_id="u-1",
            expected_xmin="3001",
            expected_goal_count=2,
        )
    deletes = [s for s, _ in conn.statements if "DELETE FROM" in s]
    assert deletes == []


# --------------------------------------------------------------- departments


def test_department_delete_locks_family_and_audits_cascade() -> None:
    conn = _FakeConnection()
    conn.next_rows = [{"indicator_id": "ind-1"}]  # locked indicator set
    conn.fetch_override = _queued_fetch(
        [
            dict(_DEPT_ROW),            # dept FOR UPDATE
            {"row_xmin": "2001"},       # xmin re-read
            {"cnt": 2},                 # goals count
            {"cnt": 24},                # monthly count
            dict(_DEPT_ROW),            # DELETE dept RETURNING
        ]
    )
    repo = PostgresStrategicIndicatorsAdminDepartmentsRepository(connection=conn)
    result = repo.delete_department(
        department_id="fin",
        actor_user_id="u-1",
        expected_xmin="2001",
        expected_indicator_count=1,
        expected_goal_count=2,
    )
    assert result["department_id"] == "fin"
    locks = [s for s, _ in conn.statements if "FOR UPDATE" in s]
    assert len(locks) == 2  # department + indicator rows
    assert "DELETE FROM strategic_indicators.departments" in "\n".join(
        s for s, _ in conn.statements
    )
    audit = [
        p for s, p in conn.statements
        if "INSERT INTO strategic_indicators.settings_audit" in s
    ]
    assert audit
    params = str(audit[0])
    assert "indicators_deleted" in params
    assert "indicator_goals_deleted" in params
    assert "monthly_targets_deleted" in params


def test_department_delete_indicator_count_mismatch_conflict() -> None:
    conn = _FakeConnection()
    conn.next_rows = [{"indicator_id": "i-1"}, {"indicator_id": "i-2"}]
    conn.fetch_override = _queued_fetch(
        [dict(_DEPT_ROW), {"row_xmin": "2001"}]
    )
    repo = PostgresStrategicIndicatorsAdminDepartmentsRepository(connection=conn)
    with pytest.raises(StrategicIndicatorsAdminConflictError):
        repo.delete_department(
            department_id="fin",
            actor_user_id="u-1",
            expected_xmin="2001",
            expected_indicator_count=1,
        )
    deletes = [s for s, _ in conn.statements if "DELETE FROM" in s]
    assert deletes == []


def test_department_delete_goal_count_mismatch_conflict() -> None:
    conn = _FakeConnection()
    conn.next_rows = [{"indicator_id": "i-1"}]
    conn.fetch_override = _queued_fetch(
        [
            dict(_DEPT_ROW),
            {"row_xmin": "2001"},
            {"cnt": 5},  # 5 goals under the dept, expected 2
        ]
    )
    repo = PostgresStrategicIndicatorsAdminDepartmentsRepository(connection=conn)
    with pytest.raises(StrategicIndicatorsAdminConflictError):
        repo.delete_department(
            department_id="fin",
            actor_user_id="u-1",
            expected_xmin="2001",
            expected_indicator_count=1,
            expected_goal_count=2,
        )
    deletes = [s for s, _ in conn.statements if "DELETE FROM" in s]
    assert deletes == []
