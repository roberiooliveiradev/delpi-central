"""W012 — owner-side optimistic-concurrency precondition contract.

Verifies the guarded mutation path with an injected fake connection: a
captured ``expected_row_xmin`` token is evaluated atomically inside the
UPDATE statement, a stale token is refused with
StrategicIndicatorsGoalConflictError, and the whole mutation commits once
inside the unit-of-work boundary.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pytest

from si_app.application.services.strategic_indicators.indicator_goal_conflict_error import (
    StrategicIndicatorsGoalConflictError,
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
    """Minimal psycopg Connection stand-in for unit tests."""

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


def _repo(conn: _FakeConnection) -> PostgresStrategicIndicatorsIndicatorGoalsRepository:
    return PostgresStrategicIndicatorsIndicatorGoalsRepository(connection=conn)


def _update(repo, conn, *, expected: str | None, row_found: bool = True) -> None:
    conn.next_row = {"id": "g-1", "row_xmin": "201"} if row_found else None
    repo.update_indicator_goal(
        goal_id="g-1",
        indicator_id=None,
        goal_year=None,
        goal_scope_branch=None,
        goal_label="Meta",
        goal_value=10.0,
        goal_periodicity="monthly",
        goal_mode="standard",
        valid_from=None,
        valid_to=None,
        notes=None,
        actor_user_id="u-1",
        expected_row_xmin=expected,
        monthly_targets=None,
    )


def test_update_guarded_sql_contains_atomic_xmin_precondition() -> None:
    conn = _FakeConnection()
    _update(_repo(conn), conn, expected="100")

    guarded = [
        (sql, params) for sql, params in conn.statements if "xmin::text = %s" in sql
    ]
    assert len(guarded) == 1
    sql, params = guarded[0]
    assert "WHERE id = %s" in sql
    assert "%s::text IS NULL OR xmin::text = %s" in sql
    assert params[-3] == "g-1"
    assert params[-2] == "100"
    assert params[-1] == "100"


def test_update_stale_token_raises_conflict_error() -> None:
    conn = _FakeConnection()
    with pytest.raises(StrategicIndicatorsGoalConflictError):
        _update(_repo(conn), conn, expected="STALE", row_found=False)


def test_update_missing_row_without_token_is_not_found() -> None:
    conn = _FakeConnection()
    with pytest.raises(ValueError, match="encontrada"):
        _update(_repo(conn), conn, expected=None, row_found=False)


def test_update_precondition_and_mutation_share_one_transaction() -> None:
    """With an injected connection the UoW defers to the caller boundary;
    the guarded UPDATE itself is a single atomic statement."""
    conn = _FakeConnection()
    _update(_repo(conn), conn, expected="100")
    # Injected connection → _unit_of_work yields without committing; the
    # caller's outer boundary owns commit/rollback (no auto-commit inside).
    assert conn.commits == 0


def test_activate_guarded_update_uses_expected_xmin() -> None:
    conn = _FakeConnection()
    repo = _repo(conn)
    # fetch_one (target lookup) and the guarded UPDATE's RETURNING both read
    # next_row; list_monthly_targets reads next_rows.
    conn.next_row = {
        "id": "g-2",
        "indicator_id": "ind-1",
        "goal_year": 2027,
        "goal_scope_branch": "01",
        "row_xmin": "301",
    }
    conn.next_rows = []
    row = repo.activate_indicator_goal(
        goal_id="g-2",
        actor_user_id="u-1",
        expected_xmin="300",
    )
    assert row["id"] == "g-2"
    guarded = [
        (sql, params)
        for sql, params in conn.statements
        if "xmin::text = %s" in sql
    ]
    assert guarded, "activate must issue a guarded UPDATE"
    _, params = guarded[0]
    assert params[-3] == "g-2"
    assert params[-2] == "300"
    assert params[-1] == "300"


def test_activate_stale_xmin_raises_conflict_before_activate() -> None:
    conn = _FakeConnection()
    repo = _repo(conn)
    target = {
        "id": "g-2",
        "indicator_id": "ind-1",
        "goal_year": 2027,
        "goal_scope_branch": "01",
    }
    rows = iter([target, None])  # fetch_one → target; guarded UPDATE → miss
    conn.fetch_override = lambda: next(rows, None)
    with pytest.raises(StrategicIndicatorsGoalConflictError):
        repo.activate_indicator_goal(
            goal_id="g-2",
            actor_user_id="u-1",
            expected_xmin="stale",
        )
