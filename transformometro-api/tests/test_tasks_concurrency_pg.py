"""Final security correction — real PostgreSQL proof of atomic task
authorization (conditional UPDATE carries actor identity + relationship).

Two real sessions driving the REAL repository/use cases with deterministic
thread barriers. Asserts invariants, not scheduling: exactly one winner per
conflicting pair, coherent loser errors (never false success), and the
final row read back authoritatively.

Runs ONLY when ``DELPI_SCRATCH_DSN`` points at a database with the
``transformometro.tm_tasks`` schema (V045+). The origin-context gating test
additionally requires the V2 room schema (access_scope/participants)::

    DELPI_SCRATCH_DSN="host=localhost dbname=delpi_scratch user=delpi password=***" \
        pytest tests/test_tasks_concurrency_pg.py
"""

from __future__ import annotations

import os
import threading
from types import SimpleNamespace
from uuid import uuid4

import pytest

psycopg = pytest.importorskip("psycopg")
from psycopg.rows import dict_row

from tm_app.application.use_cases.manage_transformometro_tasks import (
    TaskCommandUseCases,
)
from tm_app.infrastructure.persistence.repositories.task_repository import (
    TaskRepository,
)

DSN = os.getenv("DELPI_SCRATCH_DSN", "").strip()
pytestmark = pytest.mark.skipif(
    not DSN, reason="DELPI_SCRATCH_DSN not set — PG scratch unavailable"
)

S = "transformometro"
USER = str(uuid4())
OTHER = str(uuid4())
THIRD = str(uuid4())
MANAGER = str(uuid4())


def _user(user_id: str, permissions: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        permissions=permissions or ["transformometro.access"],
        is_superadmin=False,
    )


def _manager() -> SimpleNamespace:
    return _user(MANAGER, ["transformometro.access", "transformometro.manage"])


def _connect():
    return psycopg.connect(DSN, row_factory=dict_row)


def _commands() -> TaskCommandUseCases:
    return TaskCommandUseCases(TaskRepository(_connect()))


@pytest.fixture()
def pending_task():
    conn = _connect()
    task = TaskRepository(conn).create(
        title="pg-atomic",
        description=None,
        assignee_user_id=OTHER,
        created_by_user_id=USER,
        due_date=None,
    )
    conn.close()
    yield task.id
    cleanup = _connect()
    with cleanup.cursor() as cur:
        cur.execute(f"DELETE FROM {S}.tm_tasks WHERE id = %s", (task.id,))
        cleanup.commit()
    cleanup.close()


def _race(*targets) -> list[tuple[str, str]]:
    """Barrier-start callables; collect ('ok'|<exc type>, label) per thread."""
    barrier = threading.Barrier(len(targets))
    outcomes: list[tuple[str, str]] = []

    def run(fn, label):
        barrier.wait(timeout=30)
        try:
            fn()
            outcomes.append(("ok", label))
        except Exception as exc:  # noqa: BLE001 — typed outcome asserted below
            outcomes.append((type(exc).__name__, label))

    threads = [
        threading.Thread(target=run, args=(fn, label), daemon=True)
        for fn, label in targets
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert len(outcomes) == len(targets)
    return outcomes


def test_pg_stale_assignee_rejected_after_reassignment(pending_task):
    """Sequential proof: reassign commits first → the previous assignee's
    complete is rejected by the atomic WHERE, not by a stale snapshot."""
    creator = _commands()
    creator.update(
        _user(USER),
        pending_task,
        title="pg-atomic",
        description=None,
        assignee_user_id=THIRD,
        due_date=None,
    )
    with pytest.raises(PermissionError):
        _commands().complete(_user(OTHER), pending_task)
    done = _commands().complete(_user(THIRD), pending_task)
    assert done.status == "completed"
    row = TaskRepository(_connect()).get(pending_task)
    assert row.status == "completed"
    assert row.assignee_user_id == THIRD


def test_pg_concurrent_completes_single_winner(pending_task):
    outcomes = _race(
        (lambda: _commands().complete(_user(USER), pending_task), "creator"),
        (lambda: _commands().complete(_user(OTHER), pending_task), "assignee"),
    )
    oks = [o for o in outcomes if o[0] == "ok"]
    assert len(oks) == 1
    loser_kind = next(o[0] for o in outcomes if o[0] != "ok")
    assert loser_kind in {"ValueError", "PermissionError"}
    row = TaskRepository(_connect()).get(pending_task)
    assert row.status == "completed"
    assert row.completed_at is not None


def test_pg_concurrent_reassign_and_complete_coherent(pending_task):
    outcomes = _race(
        (
            lambda: _commands().update(
                _user(USER),
                pending_task,
                title="pg-atomic",
                description=None,
                assignee_user_id=THIRD,
                due_date=None,
            ),
            "reassign",
        ),
        (lambda: _commands().complete(_user(OTHER), pending_task), "complete"),
    )
    by_label = {label: kind for kind, label in outcomes}
    assert "ok" in by_label.values()
    row = TaskRepository(_connect()).get(pending_task)
    if by_label["reassign"] == "ok":
        # Reatribuição venceu: a conclusão do responsável anterior falha e o
        # estado final reflete o novo responsável ainda pendente.
        assert by_label["complete"] in {"PermissionError", "ValueError"}
        assert row.status == "pending"
        assert row.assignee_user_id == THIRD
    else:
        # Conclusão venceu: a edição não pode reverter estado terminal.
        assert by_label["complete"] == "ok"
        assert by_label["reassign"] in {"ValueError", "PermissionError"}
        assert row.status == "completed"
        assert row.assignee_user_id == OTHER


def test_pg_concurrent_cancel_and_complete_coherent(pending_task):
    outcomes = _race(
        (lambda: _commands().cancel(_user(USER), pending_task), "cancel"),
        (lambda: _commands().complete(_user(OTHER), pending_task), "complete"),
    )
    by_label = {label: kind for kind, label in outcomes}
    assert "ok" in by_label.values()
    loser = next(kind for kind, _label in outcomes if kind != "ok")
    assert loser in {"ValueError", "PermissionError"}
    row = TaskRepository(_connect()).get(pending_task)
    expected = "cancelled" if by_label["cancel"] == "ok" else "completed"
    assert row.status == expected


def test_pg_third_party_and_manager_matrix(pending_task):
    with pytest.raises(PermissionError):
        _commands().complete(_user(THIRD), pending_task)
    with pytest.raises(PermissionError):
        _commands().update(
            _user(THIRD),
            pending_task,
            title="x",
            description=None,
            assignee_user_id=THIRD,
            due_date=None,
        )
    with pytest.raises(PermissionError):
        _commands().cancel(_user(THIRD), pending_task)
    row = TaskRepository(_connect()).get(pending_task)
    assert row.status == "pending"
    assert row.assignee_user_id == OTHER
    assert row.title == "pg-atomic"
    done = _commands().complete(_manager(), pending_task)
    assert done.status == "completed"


def test_pg_origin_context_gated_by_room_membership(pending_task):
    conn = _connect()
    with conn.cursor() as cur:
        cur.execute(
            """SELECT COUNT(*) AS n
               FROM information_schema.columns
               WHERE table_schema = 'transformometro'
                 AND table_name = 'tm_interaction_rooms'
                 AND column_name = 'access_scope'"""
        )
        if cur.fetchone()["n"] == 0:
            pytest.skip("V2 room schema unavailable in scratch")
        cur.execute(
            "SELECT to_regclass('transformometro.tm_interaction_room_participants')"
        )
        if cur.fetchone()["to_regclass"] is None:
            pytest.skip("V2 room schema unavailable in scratch")
        cur.execute(
            f"""INSERT INTO {S}.tm_interaction_rooms
                    (processo_id, created_by_user_id, access_scope, title)
                SELECT p.processo_id, %s::uuid, 'members', 'pg-room'
                FROM {S}.processos p
                WHERE NOT EXISTS (
                    SELECT 1 FROM {S}.tm_interaction_rooms r
                    WHERE r.processo_id = p.processo_id)
                LIMIT 1
                RETURNING id""",
            (USER,),
        )
        room = cur.fetchone()
        if room is None:
            pytest.skip("no processo row available for room fixture")
        room_id = str(room["id"])
        cur.execute(
            f"""INSERT INTO {S}.tm_interaction_room_participants
                    (room_id, user_id, role, added_by_user_id)
                VALUES (%s::uuid, %s::uuid, 'member', %s::uuid)""",
            (room_id, OTHER, USER),
        )
        cur.execute(
            f"""INSERT INTO {S}.tm_interaction_messages
                    (room_id, author_user_id, content)
                VALUES (%s::uuid, %s::uuid, 'origem')
                RETURNING id""",
            (room_id, USER),
        )
        message_id = str(cur.fetchone()["id"])
        cur.execute(
            f"UPDATE {S}.tm_tasks SET source_interaction_message_id = %s::uuid "
            f"WHERE id = %s::uuid",
            (message_id, pending_task),
        )
        conn.commit()
    try:
        # Não-participante: room_id e rótulo suprimidos da projeção.
        suppressed = _commands().origin_contexts(_user(USER), [pending_task])
        assert suppressed[pending_task].room_id is None
        assert suppressed[pending_task].context_label is None
        # Participante: contexto resolvido.
        allowed = _commands().origin_contexts(_user(OTHER), [pending_task])
        assert allowed[pending_task].room_id == room_id
    finally:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {S}.tm_interaction_messages WHERE room_id = %s::uuid",
                (room_id,),
            )
            cur.execute(
                f"DELETE FROM {S}.tm_interaction_room_participants "
                f"WHERE room_id = %s::uuid AND user_id = %s::uuid",
                (room_id, OTHER),
            )
            cur.execute(
                f"DELETE FROM {S}.tm_interaction_rooms WHERE id = %s::uuid",
                (room_id,),
            )
            cur.execute(
                f"UPDATE {S}.tm_tasks SET source_interaction_message_id = NULL "
                f"WHERE id = %s::uuid",
                (pending_task,),
            )
            conn.commit()
        conn.close()
