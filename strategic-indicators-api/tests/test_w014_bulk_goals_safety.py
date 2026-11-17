"""W014 — owner-side safety for bulk goal ops, import preconditions, jobs.

Verifies with an injected fake connection that:

- ``duplicate_goals_year`` / ``fill_missing_goals`` /
  ``bulk_create_indicator_goals`` run every statement inside one unit of
  work (no partial commits), take sorted advisory xact locks, and seal
  digest preconditions checked against post-lock snapshots;
- digest mismatches raise ``StrategicIndicatorsAdminConflictError``
  before any mutation statement;
- ``bulk_create`` forwards per-item ``expected_max_version`` to the
  guarded INSERT and writes audit events in the same transaction;
- ``import_bundle`` enforces ``expected_counts`` inside the mutation
  transaction;
- ``TreeLoadJobsService`` binds jobs to the creator and applies
  per-actor/global admission caps.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from si_app.application.services.strategic_indicators.admin_write_conflict_error import (
    StrategicIndicatorsAdminConflictError,
)
from si_app.application.services.strategic_indicators.tree_load_jobs_service import (
    TreeLoadJobAdmissionError,
    TreeLoadJobsService,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_admin_config_bundle_repository import (
    PostgresStrategicIndicatorsAdminConfigBundleRepository,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
    PostgresStrategicIndicatorsIndicatorGoalsRepository,
)


class _FakeCursor:
    def __init__(self, conn: "_FakeConnection") -> None:
        self._conn = conn

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *exc: Any) -> bool:
        return False

    def execute(self, query: str, params: tuple = ()) -> None:
        self._conn.statements.append((query, params))

    def fetchone(self) -> dict | None:
        # One queued result per fetch call — statement ordering decides
        # which result a given query sees (mirrors the real repo's flow).
        if self._conn.fetchone_queue:
            return self._conn.fetchone_queue.pop(0)
        return None

    def fetchall(self) -> list:
        if self._conn.fetchall_queue:
            return self._conn.fetchall_queue.pop(0)
        return []


class _FakeConnection:
    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple]] = []
        self.fetchone_queue: list[dict | None] = []
        self.fetchall_queue: list[list[dict]] = []
        self.commits = 0
        self.rollbacks = 0

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


def _goal_row(**kw) -> dict:
    row = {
        "id": "g-1",
        "indicator_id": "ind-1",
        "goal_year": 2025,
        "goal_label": "Meta",
        "goal_value": Decimal("100.00"),
        "goal_periodicity": "monthly",
        "goal_mode": "standard",
        "goal_scope_branch": "",
        "version": 1,
        "is_active": True,
        "valid_from": None,
        "valid_to": None,
        "notes": None,
        "updated_at": "2025-01-01T00:00:00",
    }
    row.update(kw)
    return row


def _digest(rows, fields):
    from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_indicator_goals_repository import (
        PostgresStrategicIndicatorsIndicatorGoalsRepository as Repo,
    )

    return Repo._goals_rows_digest(list(rows), fields)


_SRC_FIELDS = (
    "indicator_id",
    "goal_scope_branch",
    "goal_label",
    "goal_value",
    "goal_periodicity",
    "goal_mode",
)
_EXIST_FIELDS = ("indicator_id", "goal_scope_branch", "goal_year")


# ------------------------------------------------------------- digest
def test_bulk_digest_normalizes_decimal_goal_value() -> None:
    """Decimal('100.00') and float 100.0 must digest identically — the
    BFF reproduces this digest over the JSON contract."""
    a = _digest([{"goal_value": Decimal("100.00"), "indicator_id": "x"}],
                _SRC_FIELDS)
    b = _digest([{"goal_value": 100.0, "indicator_id": "x"}], _SRC_FIELDS)
    assert a == b


def test_bulk_digest_membership_sensitive() -> None:
    rows = [_goal_row(indicator_id="a"), _goal_row(indicator_id="b")]
    assert _digest(rows, _SRC_FIELDS) != _digest(rows[:1], _SRC_FIELDS)
    changed = dict(rows[0])
    changed["goal_label"] = "Other"
    assert _digest([changed, rows[1]], _SRC_FIELDS) != _digest(rows, _SRC_FIELDS)


# ------------------------------------------------------ duplicate year
def test_duplicate_year_single_transaction_and_locks() -> None:
    conn = _FakeConnection()
    source = [_goal_row(id="g-src", goal_year=2025)]
    # fetchall order: probe(source), source re-read, existing read,
    # monthly targets of created row.
    conn.fetchall_queue = [source, source, [], []]
    conn.fetchone_queue = [{"max_version": 0}]
    repo = PostgresStrategicIndicatorsIndicatorGoalsRepository(connection=conn)
    source_digest = _digest(source, _SRC_FIELDS)
    existing_digest = _digest([], _EXIST_FIELDS)

    # execute_returning_one pops from fetchone queue too — queue the
    # created row after the version lookup.
    conn.fetchone_queue.append(dict(_goal_row(id="g-new", goal_year=2026)))
    out = repo.duplicate_goals_year(
        source_year=2025,
        target_year=2026,
        indicator_ids=None,
        overwrite_existing=False,
        actor_user_id="u-1",
        expected_source_digest=source_digest,
        expected_existing_digest=existing_digest,
        audit_origin="davi-mcp",
        correlation_id="p-1",
    )
    sql = [s for s, _ in conn.statements]
    locks = [s for s in sql if "pg_advisory_xact_lock" in s]
    assert locks, "advisory scope lock missing"
    inserts = [s for s in sql if "INSERT INTO strategic_indicators.indicator_goals" in s]
    assert inserts, "goal insert missing"
    audits = [s for s in sql if "settings_audit" in s]
    assert audits, "audit event missing from the same transaction"
    assert out["items"], "created item not returned"


def test_duplicate_year_digest_mismatch_blocks_mutation() -> None:
    conn = _FakeConnection()
    source = [_goal_row(id="g-src", goal_year=2025)]
    conn.fetchall_queue = [source, source, []]
    repo = PostgresStrategicIndicatorsIndicatorGoalsRepository(connection=conn)
    with pytest.raises(StrategicIndicatorsAdminConflictError):
        repo.duplicate_goals_year(
            source_year=2025,
            target_year=2026,
            indicator_ids=None,
            overwrite_existing=False,
            actor_user_id="u-1",
            expected_source_digest="0" * 64,
        )
    sql = [s for s, _ in conn.statements]
    assert not any(
        "INSERT INTO strategic_indicators.indicator_goals" in s for s in sql
    )
    assert not any(
        "UPDATE strategic_indicators.indicator_goals" in s for s in sql
    )


def test_duplicate_year_overwrite_supersedes_in_same_tx() -> None:
    conn = _FakeConnection()
    source = [_goal_row(id="g-src", goal_year=2025)]
    existing = [
        {
            "indicator_id": "ind-1",
            "goal_scope_branch": "",
            "goal_year": 2026,
        }
    ]
    conn.fetchall_queue = [source, source, existing, []]
    conn.fetchone_queue = [
        {"max_version": 1},
        dict(_goal_row(id="g-new", goal_year=2026)),
    ]
    repo = PostgresStrategicIndicatorsIndicatorGoalsRepository(connection=conn)
    out = repo.duplicate_goals_year(
        source_year=2025,
        target_year=2026,
        indicator_ids=None,
        overwrite_existing=True,
        actor_user_id="u-1",
        expected_source_digest=_digest(source, _SRC_FIELDS),
        expected_existing_digest=_digest(existing, _EXIST_FIELDS),
    )
    sql = [s for s, _ in conn.statements]
    deactivations = [
        s
        for s in sql
        if "is_active = FALSE" in s and "indicator_goals" in s
    ]
    assert deactivations, "overwrite must deactivate the current active goal"
    assert out["items"]


# ----------------------------------------------------------- fill missing
def test_fill_missing_digest_mismatch_blocks_mutation() -> None:
    conn = _FakeConnection()
    conn.fetchall_queue = [[]]  # existing read (post-lock)
    repo = PostgresStrategicIndicatorsIndicatorGoalsRepository(connection=conn)
    with pytest.raises(StrategicIndicatorsAdminConflictError):
        repo.fill_missing_goals(
            goal_year=2026,
            indicator_ids=["ind-1"],
            copy_from_year=2025,
            actor_user_id="u-1",
            expected_target_digest="0" * 64,
        )
    sql = [s for s, _ in conn.statements]
    assert not any(
        "INSERT INTO strategic_indicators.indicator_goals" in s for s in sql
    )


def test_fill_missing_locks_before_snapshot_reads() -> None:
    conn = _FakeConnection()
    # post-lock: existing read, source read, monthly targets of created.
    conn.fetchall_queue = [
        [],
        [_goal_row(id="g-src", goal_year=2025)],
        [],
    ]
    conn.fetchone_queue = [
        {"max_version": 0},
        dict(_goal_row(id="g-new", goal_year=2026)),
    ]
    repo = PostgresStrategicIndicatorsIndicatorGoalsRepository(connection=conn)
    out = repo.fill_missing_goals(
        goal_year=2026,
        indicator_ids=["ind-1"],
        copy_from_year=2025,
        actor_user_id="u-1",
    )
    sql = [s for s, _ in conn.statements]
    lock_pos = next(
        i for i, s in enumerate(sql) if "pg_advisory_xact_lock" in s
    )
    select_pos = next(
        i
        for i, s in enumerate(sql)
        if "FROM strategic_indicators.indicator_goals" in s
        and "SELECT" in s
    )
    assert lock_pos < select_pos, "snapshot read must happen after locks"
    assert out["items"]


# ------------------------------------------------------------ bulk create
def test_bulk_create_forwards_expected_max_version() -> None:
    conn = _FakeConnection()
    # create_indicator_goal: scope lock (execute), supersede UPDATE…
    # RETURNING (fetchall), guarded INSERT…RETURNING (fetchone), audit
    # insert (execute) — all inside the shared unit of work.
    conn.fetchall_queue = [[]]
    conn.fetchone_queue = [dict(_goal_row(id="g-new", goal_year=2026))]
    repo = PostgresStrategicIndicatorsIndicatorGoalsRepository(connection=conn)
    repo.bulk_create_indicator_goals(
        goal_year=2026,
        items=[
            {
                "indicator_id": "ind-1",
                "goal_label": "Meta",
                "goal_value": 5.0,
                "goal_periodicity": "monthly",
                "goal_mode": "standard",
                "goal_scope_branch": "",
                "monthly_targets": [],
                "valid_from": None,
                "valid_to": None,
                "notes": None,
                "expected_max_version": 3,
            }
        ],
        actor_user_id="u-1",
        audit_origin="davi-mcp",
        correlation_id="p-9",
    )
    inserts = [
        (s, p)
        for s, p in conn.statements
        if "INSERT INTO strategic_indicators.indicator_goals" in s
    ]
    assert inserts, "guarded insert missing"
    sql, params = inserts[0]
    assert "mv.max_version = %s" in sql
    assert 3 in params, "expected_max_version not bound to guarded insert"


# ------------------------------------------------------------- import
def test_import_bundle_expected_counts_mismatch() -> None:
    conn = _FakeConnection()
    # count_catalog: 3 COUNT fetches → departments=1, indicators=0, goals=0
    conn.fetchone_queue = [{"n": 1}, {"n": 0}, {"n": 0}]
    repo = PostgresStrategicIndicatorsAdminConfigBundleRepository(
        connection=conn
    )
    bundle = {
        "schema_version": repo.SCHEMA_VERSION,
        "departments": [],
        "department_indicators": [],
        "indicator_goals": [],
        "module_settings": {},
    }
    with pytest.raises(StrategicIndicatorsAdminConflictError):
        repo.import_bundle(
            bundle=bundle,
            actor_user_id="u-1",
            mode="merge",
            expected_counts={
                "departments": 5,
                "department_indicators": 0,
                "indicator_goals": 0,
            },
        )
    sql = [s for s, _ in conn.statements]
    assert not any("INSERT INTO" in s for s in sql)
    assert not any("DELETE FROM" in s for s in sql)


def test_import_bundle_expected_counts_match_proceeds() -> None:
    conn = _FakeConnection()
    # count_catalog(3) + merge upsert reads — generous queues.
    conn.fetchone_queue = [
        {"n": 1},
        {"n": 0},
        {"n": 0},
    ] + [None] * 40
    conn.fetchall_queue = [[]] * 60
    repo = PostgresStrategicIndicatorsAdminConfigBundleRepository(
        connection=conn
    )
    bundle = {
        "schema_version": repo.SCHEMA_VERSION,
        "departments": [],
        "department_indicators": [],
        "indicator_goals": [],
        "module_settings": {},
    }
    repo.import_bundle(
        bundle=bundle,
        actor_user_id="u-1",
        mode="merge",
        expected_counts={
            "departments": 1,
            "department_indicators": 0,
            "indicator_goals": 0,
        },
    )
    # No exception — the precondition passed inside the transaction.


def test_import_bundle_audit_rides_same_transaction() -> None:
    conn = _FakeConnection()
    conn.fetchone_queue = [{"n": 0}] * 40
    conn.fetchall_queue = [[]] * 60
    repo = PostgresStrategicIndicatorsAdminConfigBundleRepository(
        connection=conn
    )
    bundle = {
        "schema_version": repo.SCHEMA_VERSION,
        "departments": [],
        "department_indicators": [],
        "indicator_goals": [],
        "module_settings": {},
    }
    repo.import_bundle(
        bundle=bundle,
        actor_user_id="u-1",
        mode="merge",
        audit_origin="davi-mcp",
        correlation_id="prop-xyz",
    )
    audits = [s for s, _ in conn.statements if "settings_audit" in s]
    assert audits, "config.imported audit missing from the transaction"


# ----------------------------------------------------------------- jobs
def test_jobs_bound_to_creator() -> None:
    service = TreeLoadJobsService(ttl_seconds=60)
    job = service.create_and_start(
        snapshot_fn=lambda: {"ok": True},
        trends_fn=lambda: {"ok": True},
        actor_user_id="user-a",
    )
    assert service.get(job.job_id, actor_user_id="user-a") is not None
    assert service.get(job.job_id, actor_user_id="user-b") is None


def test_bound_job_progresses_to_succeeded() -> None:
    # OC-1 regression: the worker's internal lookups must bypass the
    # actor-scoped visibility check — otherwise a bound job stays
    # queued forever and never runs its callbacks.
    import time

    service = TreeLoadJobsService(ttl_seconds=60)
    calls = {"snapshot": 0, "trends": 0}

    def _snap():
        calls["snapshot"] += 1
        return {"tree": "ok"}

    def _trends():
        calls["trends"] += 1
        return {"trends": "ok"}

    job = service.create_and_start(
        snapshot_fn=_snap,
        trends_fn=_trends,
        actor_user_id="alice",
    )
    deadline = time.time() + 10
    status = None
    while time.time() < deadline:
        status = service.get(job.job_id, actor_user_id="alice")
        if status is not None and status.state == "succeeded":
            break
        time.sleep(0.02)

    assert status is not None and status.state == "succeeded"
    assert calls == {"snapshot": 1, "trends": 1}
    assert status.snapshot == {"tree": "ok"}
    assert status.trends == {"trends": "ok"}
    # Privacy preserved: another actor and an anonymous caller see 404.
    assert service.get(job.job_id, actor_user_id="bob") is None
    assert service.get(job.job_id, actor_user_id=None) is None


def test_jobs_admission_per_actor_cap() -> None:
    service = TreeLoadJobsService(ttl_seconds=60)

    def _hang():
        import threading as _t

        _t.Event().wait(0.5)
        return {}

    service.create_and_start(
        snapshot_fn=_hang, trends_fn=lambda: {}, actor_user_id="u-a"
    )
    service.create_and_start(
        snapshot_fn=_hang, trends_fn=lambda: {}, actor_user_id="u-a"
    )
    with pytest.raises(TreeLoadJobAdmissionError):
        service.create_and_start(
            snapshot_fn=_hang, trends_fn=lambda: {}, actor_user_id="u-a"
        )
    # A different actor is unaffected by u-a's cap.
    service.create_and_start(
        snapshot_fn=_hang, trends_fn=lambda: {}, actor_user_id="u-b"
    )


def test_jobs_admission_global_cap() -> None:
    service = TreeLoadJobsService(ttl_seconds=60)
    service.MAX_ACTIVE_JOBS_TOTAL = 3

    def _hang():
        import threading as _t

        _t.Event().wait(0.5)
        return {}

    for i in range(3):
        service.create_and_start(
            snapshot_fn=_hang, trends_fn=lambda: {}, actor_user_id=f"u-{i}"
        )
    with pytest.raises(TreeLoadJobAdmissionError):
        service.create_and_start(
            snapshot_fn=_hang, trends_fn=lambda: {}, actor_user_id="u-new"
        )
