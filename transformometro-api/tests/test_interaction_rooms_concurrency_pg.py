"""E3-correction P0 — real PostgreSQL concurrency proof for the R-1
guarded link removal.

Runs ONLY when ``DELPI_SCRATCH_DSN`` points at a database with the V2
interaction-room schema (e.g. the E1 scratch). Two real connections +
two threads exercise ``tombstone_link_guarded`` against ``add_message``
through the production repository — not the InMemory double.

Example:
    DELPI_SCRATCH_DSN="host=localhost dbname=delpi_e1_scratch user=delpi password=***" \
        pytest tests/test_interaction_rooms_concurrency_pg.py
"""

from __future__ import annotations

import os
import threading
import uuid
from uuid import uuid4

import pytest

psycopg = pytest.importorskip("psycopg")
from psycopg.rows import dict_row

from tm_app.domain.services.interaction_room_access_service import (
    RoomAccessExpansionBlocked,
)
from tm_app.infrastructure.persistence.repositories.interaction_room_repository import (
    InteractionRoomRepository,
)

DSN = os.getenv("DELPI_SCRATCH_DSN", "").strip()
pytestmark = pytest.mark.skipif(
    not DSN, reason="DELPI_SCRATCH_DSN not set — PG scratch unavailable"
)

S = "transformometro"
USER = str(uuid4())


def _connect():
    return psycopg.connect(DSN, row_factory=dict_row)


@pytest.fixture()
def room_and_link():
    """A members room with an active primary helpdesk_ticket link — the
    restrictive-link scenario the guard protects."""
    conn = _connect()
    room_id, link_id = uuid4(), uuid4()
    with conn.cursor() as cur:
        cur.execute(
            f"""INSERT INTO {S}.tm_interaction_rooms
                    (id, title, access_scope, created_by_user_id)
                VALUES (%s, 'pg-race', 'members', %s)""",
            (room_id, USER),
        )
        cur.execute(
            f"""INSERT INTO {S}.tm_interaction_room_links
                    (id, room_id, entity_type, entity_key, link_role, created_by_user_id)
                VALUES (%s, %s, 'helpdesk_ticket', 'pg-race-1', 'primary', %s)""",
            (link_id, room_id, USER),
        )
        conn.commit()
        yield conn, str(room_id), str(link_id)
        cur.execute(
            f"DELETE FROM {S}.tm_interaction_room_links WHERE room_id = %s",
            (room_id,),
        )
        cur.execute(
            f"DELETE FROM {S}.tm_interaction_messages WHERE room_id = %s",
            (room_id,),
        )
        cur.execute(
            f"DELETE FROM {S}.tm_interaction_rooms WHERE id = %s", (room_id,)
        )
        conn.commit()
    conn.close()


def test_pg_guarded_removal_serializes_concurrent_writer(room_and_link):
    """Two real sessions: the remover holds FOR UPDATE through its whole
    critical section — the writer's INSERT waits for the commit, never
    slips between recount and tombstone."""
    setup_conn, room_id, link_id = room_and_link
    remover = InteractionRoomRepository(_connect())
    writer = InteractionRoomRepository(_connect())
    entered = threading.Event()
    release = threading.Event()

    outcome: dict = {}
    errors: dict = {}

    def slow_removal():
        conn = remover._injected_connection
        try:
            remover._lock_room(conn, room_id)
            entered.set()
            assert release.wait(10)
            link = remover.tombstone_link(link_id, cause="explicit")
            conn.commit()
            outcome["link"] = link
        except Exception as exc:  # noqa: BLE001 - test evidence
            conn.rollback()
            errors["rem"] = exc

    def write_message():
        try:
            msg = writer.add_message(
                room_id=room_id, author_user_id=USER, content="pg-race-write"
            )
            outcome["msg"] = msg
        except Exception as exc:  # noqa: BLE001
            errors["writer"] = exc

    t_rem = threading.Thread(target=slow_removal)
    t_rem.start()
    assert entered.wait(10)
    t_w = threading.Thread(target=write_message)
    t_w.start()
    t_w.join(timeout=2)
    assert t_w.is_alive(), "writer must block on the room row lock"
    release.set()
    t_rem.join(10)
    t_w.join(10)
    assert not errors, errors
    assert outcome["link"].deleted_at is not None
    assert outcome["msg"].id
    # consistent state: link tombstoned, message landed post-commit
    row = setup_conn.execute(
        f"SELECT deleted_at FROM {S}.tm_interaction_room_links WHERE id = %s",
        (link_id,),
    ).fetchone()
    assert row["deleted_at"] is not None
    remover._injected_connection.close()
    writer._injected_connection.close()


def test_pg_guarded_removal_blocked_by_existing_history(room_and_link):
    setup_conn, room_id, link_id = room_and_link
    repo = InteractionRoomRepository(_connect())
    repo.add_message(room_id=room_id, author_user_id=USER, content="history")
    try:
        with pytest.raises(RoomAccessExpansionBlocked):
            repo.tombstone_link_guarded(
                room_id=room_id, link_id=link_id, cause="explicit"
            )
    finally:
        repo._injected_connection.rollback()
        repo._injected_connection.close()
    row = setup_conn.execute(
        f"SELECT deleted_at FROM {S}.tm_interaction_room_links WHERE id = %s",
        (link_id,),
    ).fetchone()
    assert row["deleted_at"] is None
