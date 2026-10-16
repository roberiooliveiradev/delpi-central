"""E3 final security correction — real PostgreSQL proof that a write
authorized over a stale context is rejected.

Two real sessions + the REAL production use cases
(``InteractionRoomUseCases.post_message`` / ``remove_link`` /
``remove_participant``) and persistence methods — not repository
primitives. Deterministic barriers coordinate the interleavings the
review demanded.

Runs ONLY when ``DELPI_SCRATCH_DSN`` points at a database with the V2
interaction-room schema (e.g. the E1 scratch)::

    DELPI_SCRATCH_DSN="host=localhost dbname=delpi_e1_scratch user=delpi password=***" \
        pytest tests/test_interaction_rooms_concurrency_pg.py
"""

from __future__ import annotations

import os
import threading
from types import SimpleNamespace
from uuid import uuid4

import pytest

psycopg = pytest.importorskip("psycopg")
from psycopg.rows import dict_row

from tm_app.application.use_cases.manage_interaction_rooms import (
    InteractionRoomUseCases,
)
from tm_app.domain.services.interaction_room_access_service import (
    LINK_STATE_VISIBLE,
    RoomAccessExpansionBlocked,
    StaleRoomAuthorization,
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


def _user(user_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        permissions=["transformometro.access"],
        is_superadmin=False,
    )


class _GateTickets:
    """TicketVisibilityPort double that also acts as the deterministic
    barrier: the writer's authorization pauses inside the external
    probe — after authz, before the repository write — exactly the
    window the stale check protects."""

    def __init__(self) -> None:
        self.authorized = threading.Event()
        self.release = threading.Event()

    def check_ticket_visibility(self, authorization, ticket_key):
        self.authorized.set()
        self.release.wait(10)
        return LINK_STATE_VISIBLE


class _VisibleTickets:
    """Always-visible ticket authority — no barrier."""

    def check_ticket_visibility(self, authorization, ticket_key):
        return LINK_STATE_VISIBLE


def _connect():
    return psycopg.connect(DSN, row_factory=dict_row)


@pytest.fixture()
def ticket_room():
    """A members room: USER owner-participant, OTHER member, restrictive
    primary helpdesk_ticket link — the R-1 removal scenario."""
    conn = _connect()
    repo = InteractionRoomRepository(conn)
    room = repo.create_room_graph(
        title="pg-stale",
        access_scope="members",
        created_by_user_id=USER,
        links=(("helpdesk_ticket", f"pg-stale-{uuid4().hex[:8]}", "primary"),),
        owner_participant=True,
        participant_ids=(OTHER,),
    )
    conn.close()
    link_id = room.links[0].id
    yield room.id, link_id
    cleanup = _connect()
    with cleanup.cursor() as cur:
        cur.execute(
            f"DELETE FROM {S}.tm_interaction_reads WHERE room_id = %s", (room.id,)
        )
        cur.execute(
            f"DELETE FROM {S}.tm_interaction_messages WHERE room_id = %s", (room.id,)
        )
        cur.execute(
            f"DELETE FROM {S}.tm_interaction_room_participants WHERE room_id = %s",
            (room.id,),
        )
        cur.execute(
            f"DELETE FROM {S}.tm_interaction_room_links WHERE room_id = %s",
            (room.id,),
        )
        cur.execute(
            f"DELETE FROM {S}.tm_interaction_rooms WHERE id = %s", (room.id,)
        )
        cleanup.commit()
    cleanup.close()


def test_pg_scenario_a_removal_commits_first_rejects_stale_write(ticket_room):
    """Review scenario A — removal first:

    writer authorized while the restrictive link is active → writer
    waits before acquiring the lock → remover locks, recounts (0),
    tombstones, COMMITS → writer acquires the lock → detects the stale
    authorization → fails, zero persisted rows.
    """
    room_id, link_id = ticket_room
    gate = _GateTickets()
    writer_cases = InteractionRoomUseCases(
        InteractionRoomRepository(_connect()), ticket_visibility=gate
    )
    remover_cases = InteractionRoomUseCases(
        InteractionRoomRepository(_connect())
    )
    outcome: dict = {}
    errors: dict = {}

    def writer():
        try:
            outcome["msg"] = writer_cases.post_message(
                _user(USER), room_id, "stale write", authorization="Bearer w"
            )
        except StaleRoomAuthorization as exc:
            outcome["stale"] = exc
        except Exception as exc:  # noqa: BLE001 - evidence
            errors["writer"] = exc

    def remover():
        assert gate.authorized.wait(10)
        try:
            remover_cases.remove_link(_user(USER), room_id, link_id)
            outcome["removed"] = True
        except Exception as exc:  # noqa: BLE001
            errors["remover"] = exc
        finally:
            gate.release.set()

    t_w = threading.Thread(target=writer)
    t_w.start()
    t_r = threading.Thread(target=remover)
    t_r.start()
    t_w.join(15)
    t_r.join(15)
    assert not errors, errors
    assert "stale" in outcome and "msg" not in outcome, outcome
    assert outcome["removed"] is True

    check = _connect()
    with check.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) AS n FROM {S}.tm_interaction_messages WHERE room_id = %s",
            (room_id,),
        )
        assert cur.fetchone()["n"] == 0
        cur.execute(
            f"SELECT COUNT(*) AS n FROM {S}.tm_interaction_reads WHERE room_id = %s",
            (room_id,),
        )
        assert cur.fetchone()["n"] == 0
        cur.execute(
            f"SELECT deleted_at FROM {S}.tm_interaction_room_links WHERE id = %s",
            (link_id,),
        )
        assert cur.fetchone()["deleted_at"] is not None
    check.close()


def test_pg_scenario_b_writer_commits_first_blocks_removal(ticket_room):
    """Review scenario B — writer first:

    writer acquires the room lock and holds it inside the critical
    section → remover waits → writer revalidates (unchanged), persists,
    COMMITS → remover acquires the lock → recount sees history →
    room_access_expansion_blocked → link stays active.
    """
    room_id, link_id = ticket_room
    inside = threading.Event()
    release = threading.Event()
    writer_conn = _connect()
    writer_repo = InteractionRoomRepository(writer_conn)
    real_assert = InteractionRoomRepository._assert_authorization_current

    def pausing_assert(connection, rid, expected, *, actor_user_id=None):
        inside.set()
        assert release.wait(10)
        return real_assert(
            connection, rid, expected, actor_user_id=actor_user_id
        )

    writer_repo._assert_authorization_current = pausing_assert
    writer_cases = InteractionRoomUseCases(
        writer_repo, ticket_visibility=_VisibleTickets()
    )
    remover_cases = InteractionRoomUseCases(
        InteractionRoomRepository(_connect())
    )
    outcome: dict = {}
    errors: dict = {}

    def writer():
        try:
            outcome["msg"] = writer_cases.post_message(
                _user(USER), room_id, "lands first", authorization="Bearer w"
            )
        except Exception as exc:  # noqa: BLE001
            errors["writer"] = exc

    def remover():
        assert inside.wait(10)
        try:
            remover_cases.remove_link(_user(USER), room_id, link_id)
        except RoomAccessExpansionBlocked as exc:
            outcome["blocked"] = exc
        except Exception as exc:  # noqa: BLE001
            errors["remover"] = exc

    t_w = threading.Thread(target=writer)
    t_w.start()
    t_r = threading.Thread(target=remover)
    t_r.start()
    t_r.join(timeout=2)
    assert t_r.is_alive(), "remover must block on the room lock"
    release.set()
    t_w.join(15)
    t_r.join(15)
    assert not errors, errors
    assert outcome["msg"].id
    assert "blocked" in outcome, outcome

    check = _connect()
    with check.cursor() as cur:
        cur.execute(
            f"SELECT deleted_at FROM {S}.tm_interaction_room_links WHERE id = %s",
            (link_id,),
        )
        assert cur.fetchone()["deleted_at"] is None
        cur.execute(
            f"SELECT COUNT(*) AS n FROM {S}.tm_interaction_messages WHERE room_id = %s",
            (room_id,),
        )
        assert cur.fetchone()["n"] == 1
    check.close()
    writer_conn.close()


def test_pg_scenario_c_participant_removal_stales_write(ticket_room):
    """Section 4 — authorizing-state mutation beyond links:

    OTHER is authorized as a member → waits → admin removes OTHER's
    participation under the room lock and commits → OTHER's locked
    write detects the revoked participation → StaleRoomAuthorization,
    zero rows.
    """
    room_id, _link_id = ticket_room
    gate = _GateTickets()
    writer_cases = InteractionRoomUseCases(
        InteractionRoomRepository(_connect()), ticket_visibility=gate
    )
    admin_cases = InteractionRoomUseCases(
        InteractionRoomRepository(_connect())
    )
    outcome: dict = {}
    errors: dict = {}

    def writer():
        try:
            outcome["msg"] = writer_cases.post_message(
                _user(OTHER), room_id, "stale member", authorization="Bearer o"
            )
        except StaleRoomAuthorization as exc:
            outcome["stale"] = exc
        except Exception as exc:  # noqa: BLE001
            errors["writer"] = exc

    def admin():
        assert gate.authorized.wait(10)
        try:
            admin_cases.remove_participant(_user(USER), room_id, OTHER)
            outcome["removed"] = True
        except Exception as exc:  # noqa: BLE001
            errors["admin"] = exc
        finally:
            gate.release.set()

    t_w = threading.Thread(target=writer)
    t_w.start()
    t_a = threading.Thread(target=admin)
    t_a.start()
    t_w.join(15)
    t_a.join(15)
    assert not errors, errors
    assert "stale" in outcome and "msg" not in outcome, outcome
    assert outcome["removed"] is True

    check = _connect()
    with check.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) AS n FROM {S}.tm_interaction_messages WHERE room_id = %s",
            (room_id,),
        )
        assert cur.fetchone()["n"] == 0
    check.close()


def test_pg_scenario_d_removed_member_edit_is_rejected(ticket_room):
    """Actor-membership coverage: the stale check propagates the writer's
    identity — an authorized edit whose actor loses participation before
    the lock must fail closed with stale_authorization_context and
    zero mutation."""
    room_id, _link_id = ticket_room
    setup_repo = InteractionRoomRepository(_connect())
    seeded = setup_repo.add_message(
        room_id=room_id, author_user_id=OTHER, content="original"
    )
    setup_repo._injected_connection.close()

    paused = threading.Event()
    release = threading.Event()
    writer_repo = InteractionRoomRepository(_connect())
    real_update = writer_repo.update_message

    def pausing_update(**kwargs):
        # pause AFTER the use case's authorization, BEFORE the lock
        paused.set()
        assert release.wait(10)
        return real_update(**kwargs)

    writer_repo.update_message = pausing_update
    writer_cases = InteractionRoomUseCases(
        writer_repo, ticket_visibility=_VisibleTickets()
    )
    admin_cases = InteractionRoomUseCases(
        InteractionRoomRepository(_connect())
    )
    outcome: dict = {}
    errors: dict = {}

    def writer():
        try:
            outcome["msg"] = writer_cases.edit_message(
                _user(OTHER), room_id, seeded.id, "stale edit",
                authorization="Bearer o",
            )
        except StaleRoomAuthorization as exc:
            outcome["stale"] = exc
        except Exception as exc:  # noqa: BLE001
            errors["writer"] = exc

    def admin():
        assert paused.wait(10)
        try:
            admin_cases.remove_participant(_user(USER), room_id, OTHER)
            outcome["removed"] = True
        except Exception as exc:  # noqa: BLE001
            errors["admin"] = exc
        finally:
            release.set()

    t_w = threading.Thread(target=writer)
    t_w.start()
    t_a = threading.Thread(target=admin)
    t_a.start()
    t_w.join(15)
    t_a.join(15)
    assert not errors, errors
    assert "stale" in outcome and "msg" not in outcome, outcome
    assert outcome["removed"] is True

    check = _connect()
    with check.cursor() as cur:
        cur.execute(
            f"SELECT content, edited_at FROM {S}.tm_interaction_messages WHERE id = %s",
            (seeded.id,),
        )
        row = cur.fetchone()
        assert row["content"] == "original"
        assert row["edited_at"] is None
    check.close()
    writer_repo._injected_connection.close()
