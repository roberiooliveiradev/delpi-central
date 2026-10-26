"""Inbox filters and message reads — real PostgreSQL proof that the
repository honors ``inbox_filter`` on whatever schema the connected
database actually carries, and that the authorized read chain
``can_view_room -> get_room -> list_messages`` holds end to end.

Runs ONLY when ``DELPI_SCRATCH_DSN`` points at a scratch database.
Expectations adapt to the schema found at runtime:

- satellites present (``tm_interaction_reads`` + ``tm_interaction_mentions``)
  -> full filter semantics verified;
- satellites absent (true legacy) -> ``all`` still lists rooms with
  neutral signals, but ``unread``/``mentioned`` return ``[]`` — the
  adapter must never presume state it cannot prove.

- links/participants present (V2 contract) -> members-scope filtering
  verified through the canonical use case.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from uuid import uuid4

import pytest

psycopg = pytest.importorskip("psycopg")
from psycopg.rows import dict_row

from tm_app.application.security.authorization_policy import (
    AuthorizationDenied,
)
from tm_app.application.use_cases.manage_interaction_rooms import (
    InteractionRoomUseCases,
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
OTHER = str(uuid4())


def _user(user_id: str, permissions: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        permissions=["transformometro.access"] if permissions is None else permissions,
        is_superadmin=False,
    )


def _connect():
    return psycopg.connect(DSN, row_factory=dict_row)


def _table_exists(conn, table: str) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass(%s) AS reg", (f"{S}.{table}",))
        return bool(cur.fetchone()["reg"])


def _columns(conn, table: str) -> frozenset[str]:
    with conn.cursor() as cur:
        cur.execute(
            """SELECT column_name FROM information_schema.columns
               WHERE table_schema = %s AND table_name = %s""",
            (S, table),
        )
        return frozenset(r["column_name"] for r in cur.fetchall())


@pytest.fixture()
def seeded_rooms():
    """Two rooms on the connected schema, whatever it is: room A carries a
    message authored by OTHER (unread for USER) plus a USER mention when
    the satellite exists; room B carries only USER's own message."""
    conn = _connect()
    room_cols = _columns(conn, "tm_interaction_rooms")
    room_a, room_b = str(uuid4()), str(uuid4())
    msg_a, msg_b = str(uuid4()), str(uuid4())
    has_reads = _table_exists(conn, "tm_interaction_reads")
    has_mentions = _table_exists(conn, "tm_interaction_mentions")
    has_v2 = "access_scope" in room_cols

    def room_insert(room_id: str) -> None:
        cols, vals = ["id", "created_by_user_id"], [room_id, USER]
        if "access_scope" in room_cols:
            cols.append("access_scope")
            vals.append("open")
        if "deleted_at" in room_cols:
            cols.append("deleted_at")
            vals.append(None)
        uuid_cols = {"id", "created_by_user_id"}
        placeholders = ", ".join(
            "%s::uuid" if c in uuid_cols else "%s" for c in cols
        )
        with conn.cursor() as cur:
            cur.execute(
                f"""INSERT INTO {S}.tm_interaction_rooms ({", ".join(cols)})
                    VALUES ({placeholders})""",
                tuple(vals),
            )

    def message_insert(message_id: str, room_id: str, author: str, content: str) -> None:
        with conn.cursor() as cur:
            cur.execute(
                f"""INSERT INTO {S}.tm_interaction_messages
                        (id, room_id, author_user_id, content)
                    VALUES (%s::uuid, %s::uuid, %s::uuid, %s)""",
                (message_id, room_id, author, content),
            )

    with conn.cursor() as cur:
        room_insert(room_a)
        room_insert(room_b)
        message_insert(msg_a, room_a, OTHER, "inbox-pg message from other")
        message_insert(msg_b, room_b, USER, "inbox-pg own message")
        if has_mentions:
            cur.execute(
                f"""INSERT INTO {S}.tm_interaction_mentions
                        (message_id, mentioned_user_id, label)
                    VALUES (%s::uuid, %s::uuid, %s)""",
                (msg_a, USER, "@user"),
            )
        conn.commit()

    yield {
        "room_a": room_a,
        "room_b": room_b,
        "msg_a": msg_a,
        "has_reads": has_reads,
        "has_mentions": has_mentions,
        "has_v2": has_v2,
    }

    cleanup = _connect()
    with cleanup.cursor() as cur:
        for table in (
            "tm_interaction_mentions",
            "tm_interaction_reactions",
            "tm_interaction_pins",
            "tm_interaction_reads",
            "tm_interaction_attachments",
            "tm_interaction_room_participants",
            "tm_interaction_room_links",
        ):
            if _table_exists(cleanup, table):
                cur.execute(
                    f"DELETE FROM {S}.{table} WHERE room_id IN (%s::uuid, %s::uuid)"
                    if "room_id" in _columns(cleanup, table)
                    else f"DELETE FROM {S}.{table} WHERE message_id IN "
                         f"(SELECT id FROM {S}.tm_interaction_messages "
                         f"WHERE room_id IN (%s::uuid, %s::uuid))",
                    (room_a, room_b),
                )
        cur.execute(
            f"DELETE FROM {S}.tm_interaction_messages WHERE room_id IN (%s::uuid, %s::uuid)",
            (room_a, room_b),
        )
        cur.execute(
            f"DELETE FROM {S}.tm_interaction_rooms WHERE id IN (%s::uuid, %s::uuid)",
            (room_a, room_b),
        )
        cleanup.commit()
    cleanup.close()
    conn.close()


def test_inbox_all_lists_rooms_with_available_signals(seeded_rooms):
    repo = InteractionRoomRepository(_connect())
    rooms = {r.id: r for r in repo.list_rooms(viewer_user_id=USER, inbox_filter="all")}
    assert seeded_rooms["room_a"] in rooms
    assert seeded_rooms["room_b"] in rooms
    if seeded_rooms["has_reads"]:
        # OTHER's message is unread for USER; USER's own message never counts.
        assert rooms[seeded_rooms["room_a"]].unread_count >= 1
        assert rooms[seeded_rooms["room_b"]].unread_count == 0
    else:
        assert rooms[seeded_rooms["room_a"]].unread_count == 0
    if seeded_rooms["has_mentions"]:
        assert rooms[seeded_rooms["room_a"]].mentioned is True
        assert rooms[seeded_rooms["room_b"]].mentioned is False
    else:
        assert rooms[seeded_rooms["room_a"]].mentioned is False


def test_inbox_unread_filter(seeded_rooms):
    repo = InteractionRoomRepository(_connect())
    ids = {r.id for r in repo.list_rooms(viewer_user_id=USER, inbox_filter="unread")}
    if seeded_rooms["has_reads"]:
        assert seeded_rooms["room_a"] in ids
        assert seeded_rooms["room_b"] not in ids
    else:
        # No mechanism can prove unread state — never presume every room
        # is unread. Empty is the only honest answer.
        assert ids == set()


def test_inbox_mentioned_filter(seeded_rooms):
    repo = InteractionRoomRepository(_connect())
    ids = {r.id for r in repo.list_rooms(viewer_user_id=USER, inbox_filter="mentioned")}
    if seeded_rooms["has_mentions"]:
        assert seeded_rooms["room_a"] in ids
        assert seeded_rooms["room_b"] not in ids
    else:
        assert ids == set()


def test_authorized_read_chain_messages(seeded_rooms):
    uc = InteractionRoomUseCases(InteractionRoomRepository(_connect()))
    room_id = seeded_rooms["room_a"]
    assert uc.can_view_room(_user(USER), room_id, authorization=None) is True
    room = uc.get_room(_user(USER), room_id, authorization=None)
    assert room.id == room_id
    out = uc.list_messages(_user(USER), room_id, authorization=None)
    assert len(out["items"]) >= 1
    assert out["items"][0]["content"] == "inbox-pg message from other"


def test_denied_identity_fails_closed_on_messages(seeded_rooms):
    uc = InteractionRoomUseCases(InteractionRoomRepository(_connect()))
    room_id = seeded_rooms["room_a"]
    outsider = _user(OTHER, permissions=[])
    assert uc.can_view_room(outsider, room_id, authorization=None) is False
    with pytest.raises(AuthorizationDenied):
        uc.get_room(outsider, room_id, authorization=None)
    with pytest.raises(AuthorizationDenied):
        uc.list_messages(outsider, room_id, authorization=None)


def test_message_pagination(seeded_rooms):
    conn = _connect()
    repo = InteractionRoomRepository(conn)
    extra_ids = [str(uuid4()) for _ in range(2)]
    with conn.cursor() as cur:
        for mid in extra_ids:
            cur.execute(
                f"""INSERT INTO {S}.tm_interaction_messages
                        (id, room_id, author_user_id, content)
                    VALUES (%s::uuid, %s::uuid, %s::uuid, %s)""",
                (mid, seeded_rooms["room_a"], OTHER, "inbox-pg extra"),
            )
        conn.commit()
    try:
        first, has_more = repo.list_messages(seeded_rooms["room_a"], limit=2)
        assert len(first) == 2
        assert has_more is True
        older, has_more_2 = repo.list_messages(
            seeded_rooms["room_a"], limit=2, before_id=first[0].id
        )
        assert len(older) >= 1
        assert all(m.id != first[0].id for m in older)
    finally:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {S}.tm_interaction_messages WHERE id = ANY(%s::uuid[])",
                (extra_ids,),
            )
            conn.commit()
        conn.close()


def test_members_scope_filters_nonparticipant_inbox(seeded_rooms):
    if not seeded_rooms["has_v2"]:
        pytest.skip("V2 contract tables absent — scope filtering n/a")
    conn = _connect()
    repo = InteractionRoomRepository(conn)
    room = repo.create_room_graph(
        title="inbox-pg members",
        access_scope="members",
        created_by_user_id=USER,
        links=(),
        owner_participant=True,
        participant_ids=(),
    )
    try:
        uc = InteractionRoomUseCases(InteractionRoomRepository(_connect()))
        assert any(r.id == room.id for r in uc.list_rooms(_user(USER)))
        assert not any(r.id == room.id for r in uc.list_rooms(_user(OTHER)))
        assert uc.can_view_room(_user(OTHER), room.id, authorization=None) is False
    finally:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {S}.tm_interaction_room_participants WHERE room_id = %s::uuid",
                (room.id,),
            )
            cur.execute(
                f"DELETE FROM {S}.tm_interaction_room_links WHERE room_id = %s::uuid",
                (room.id,),
            )
            cur.execute(
                f"DELETE FROM {S}.tm_interaction_rooms WHERE id = %s::uuid",
                (room.id,),
            )
            conn.commit()
        conn.close()
