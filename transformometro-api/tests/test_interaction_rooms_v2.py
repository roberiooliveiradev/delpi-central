"""Interaction Rooms V2 — negative-security & lifecycle suite (T-01…T-15).

Controlled doubles only: the real Postgres adapter is exercised through
the E1 preflight evidence, not here. Integration scenarios that need the
V056 schema are declared TEST_NOT_RUN in the execution report — unit
coverage proves the domain/application rules.
"""

from __future__ import annotations

import json
import threading
import time
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
)
from tm_app.application.use_cases.manage_interaction_rooms import InteractionRoomUseCases
from tm_app.domain.services.interaction_room_access_service import (
    LINK_STATE_NOT_FOUND,
    LINK_STATE_RESTRICTED,
    LINK_STATE_SESSION_MISSING,
    LINK_STATE_UNAVAILABLE,
    LINK_STATE_VISIBLE,
    PrimaryLinkConflict,
    RoomAccessExpansionBlocked,
    RoomAnchorLinkRemovalLocked,
    RoomAuthorizationDenied,
    StaleRoomAuthorization,
)
from tm_app.infrastructure.persistence.repositories.interaction_room_repository import (
    InMemoryInteractionRoomRepository,
)

USER = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"
THIRD = "66666666-6666-6666-6666-666666666666"
PROCESS = "33333333-3333-3333-3333-333333333333"
PROCESS_B = "44444444-4444-4444-4444-444444444444"
TICKET = "1275"
BEARER = "Bearer test"


def _user(*, permissions=None, user_id=USER):
    return SimpleNamespace(
        id=user_id,
        permissions=[ACCESS_PERMISSION] if permissions is None else permissions,
        is_superadmin=False,
    )


def _manager(user_id=THIRD):
    return _user(permissions=[ACCESS_PERMISSION, MANAGE_PERMISSION], user_id=user_id)


class FakeTicketVisibility:
    """TicketVisibilityPort double — mutable per-ticket link-state map."""

    def __init__(self, states: dict[str, str] | None = None, default: str = LINK_STATE_VISIBLE):
        self.states = states or {}
        self.default = default
        self.calls: list[tuple[str | None, str]] = []

    def check_ticket_visibility(self, authorization: str, ticket_key: str) -> str:
        self.calls.append((authorization, ticket_key))
        if not authorization:
            return LINK_STATE_SESSION_MISSING
        return self.states.get(ticket_key, self.default)


class FakeAudit:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    def log(self, **kwargs) -> None:
        self.entries.append(kwargs)


def _cases(
    default: str = LINK_STATE_VISIBLE,
) -> tuple[InteractionRoomUseCases, InMemoryInteractionRoomRepository, FakeTicketVisibility, FakeAudit]:
    repo = InMemoryInteractionRoomRepository()
    repo.processes.update({PROCESS, PROCESS_B})
    tickets = FakeTicketVisibility(default=default)
    audit = FakeAudit()
    cases = InteractionRoomUseCases(repo, ticket_visibility=tickets, audit=audit)
    return cases, repo, tickets, audit


def _ticket_room(cases: InteractionRoomUseCases, user=None, ticket=TICKET):
    return cases.open_for_ticket(user or _user(), ticket, authorization=BEARER)


# --- T-01: restrictive ticket room denies access-only users ----------------


def test_ticket_room_denies_user_without_ticket_acl():
    cases, repo, tickets, _ = _cases()
    room = _ticket_room(cases)
    cases.post_message(_user(), room.id, "contexto do chamado", authorization=BEARER)

    # ACL revoked / never held: access permission alone is not enough.
    tickets.states[TICKET] = LINK_STATE_RESTRICTED
    with pytest.raises(RoomAuthorizationDenied) as denied:
        cases.get_room(_user(user_id=OTHER), room.id, authorization=BEARER)
    assert denied.value.status_code == 404
    assert denied.value.error_code == "not_found"
    with pytest.raises(RoomAuthorizationDenied):
        cases.list_messages(_user(user_id=OTHER), room.id, authorization=BEARER)
    assert [item.id for item in cases.list_rooms(_user(user_id=OTHER), authorization=BEARER)] == []


def test_revoked_ticket_acl_blocks_owner_read():
    """Revocation must block reads — fresh authority evaluation per call."""
    cases, _, tickets, _ = _cases()
    room = _ticket_room(cases)
    cases.post_message(_user(), room.id, "segredo", authorization=BEARER)
    tickets.states[TICKET] = LINK_STATE_RESTRICTED
    with pytest.raises(RoomAuthorizationDenied):
        cases.get_room(_user(), room.id, authorization=BEARER)


# --- T-02: reference restricts exactly like primary ------------------------


def test_reference_link_restricts_like_primary():
    cases, repo, tickets, _ = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    cases.post_message(_user(), room.id, "análise", authorization=BEARER)
    link = cases.add_link(
        _user(), room.id, "helpdesk_ticket", TICKET,
        link_role="reference", authorization=BEARER,
    )
    assert link.link_role == "reference"

    tickets.states[TICKET] = LINK_STATE_RESTRICTED
    with pytest.raises(RoomAuthorizationDenied) as denied:
        cases.get_room(_user(), room.id, authorization=BEARER)
    assert denied.value.status_code == 404


# --- T-03: removed participant loses every surface --------------------------


def test_removed_participant_loses_all_surfaces(tmp_path):
    cases, repo, tickets, _ = _cases()
    room = cases.open_standalone(_user(), "War room", participant_ids=[OTHER])
    member = _user(user_id=OTHER)
    cases.post_message(member, room.id, "nota do membro")
    assert cases.get_room(member, room.id).id == room.id
    assert cases.list_messages(member, room.id)["items"]

    cases.remove_participant(_user(), room.id, OTHER)
    with pytest.raises(RoomAuthorizationDenied) as denied:
        cases.get_room(member, room.id)
    assert denied.value.status_code == 404
    with pytest.raises(RoomAuthorizationDenied):
        cases.list_messages(member, room.id)
    with pytest.raises(RoomAuthorizationDenied):
        cases.list_attachments(member, room.id)
    assert [item.id for item in cases.list_rooms(member)] == []


def test_owner_participant_cannot_be_removed():
    cases, _, _, _ = _cases()
    room = cases.open_standalone(_user(), "Minha sala")
    with pytest.raises(PermissionError):
        cases.remove_participant(_user(), room.id, USER)


# --- T-05/T-11: expansion rule (R-1) ----------------------------------------


def test_remove_restrictive_link_with_history_is_blocked():
    cases, repo, tickets, _ = _cases()
    room = _ticket_room(cases)
    cases.post_message(_user(), room.id, "histórico protegido", authorization=BEARER)
    link = next(l for l in repo.list_links(room.id) if l.entity_type == "helpdesk_ticket")

    for actor in (_user(), _manager()):
        with pytest.raises(RoomAccessExpansionBlocked) as blocked:
            cases.remove_link(actor, room.id, link.id)
        assert blocked.value.error_code == "room_access_expansion_blocked"
        assert blocked.value.status_code == 409


def test_tombstoned_history_still_blocks_link_removal():
    """Visible-message count is not proof of empty history (R-1)."""
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    msg = cases.post_message(_user(), room.id, "apagada depois", authorization=BEARER)
    cases.delete_message(_user(), room.id, msg.id, authorization=BEARER)  # tombstone only
    link = next(l for l in repo.list_links(room.id) if l.entity_type == "helpdesk_ticket")
    with pytest.raises(RoomAccessExpansionBlocked):
        cases.remove_link(_user(), room.id, link.id)


def test_remove_restrictive_link_without_content_is_allowed():
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    link = next(l for l in repo.list_links(room.id) if l.entity_type == "helpdesk_ticket")
    cases.remove_link(_user(), room.id, link.id)
    tomb = repo.list_links(room.id, include_inactive=True)
    assert tomb[0].deleted_cause == "explicit"
    # room survives as members-only standalone — no link checks remain
    assert cases.get_room(_user(), room.id).id == room.id


def test_remove_process_link_does_not_expand_and_is_allowed():
    """Process ACL is the platform `access` scope today — removing it does
    not widen the effective audience beyond who already qualified."""
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "temporária")
    cases.post_message(_user(), room.id, "histórico")
    link = cases.add_link(_user(), room.id, "process", PROCESS, link_role="reference")
    cases.remove_link(_user(), room.id, link.id)
    assert all(not l.active for l in repo.list_links(room.id, include_inactive=True))


# --- T-07: cardinality -------------------------------------------------------


def test_duplicate_active_primary_claim_conflicts():
    cases, repo, _, _ = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    other = cases.open_for_process(_user(), PROCESS_B)
    with pytest.raises(PrimaryLinkConflict) as conflict:
        cases.add_link(_user(), other.id, "process", PROCESS, link_role="primary")
    assert conflict.value.error_code == "primary_link_conflict"


def test_one_room_can_be_primary_for_many_objects():
    cases, repo, _, _ = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    cases.add_link(_user(), room.id, "process", PROCESS_B, link_role="primary")
    cases.add_link(
        _user(), room.id, "helpdesk_ticket", TICKET,
        link_role="primary", authorization=BEARER,
    )
    roles = {
        (l.entity_type, l.link_role)
        for l in repo.list_links(room.id)
        if l.link_role == "primary" and l.active
    }
    assert ("process", "primary") in roles
    assert ("helpdesk_ticket", "primary") in roles
    # and references still coexist
    cases.add_link(_user(), room.id, "helpdesk_ticket", "9900", link_role="reference", authorization=BEARER)


# --- T-08: multi-primary room, open_or_locate deny without duplicating -------


def test_open_or_locate_denies_without_creating_duplicate():
    cases, repo, tickets, _ = _cases()
    room = _ticket_room(cases)
    cases.add_link(_user(), room.id, "process", PROCESS, link_role="primary", authorization=BEARER)
    tickets.states[TICKET] = LINK_STATE_RESTRICTED

    room_count = len(repo.rooms)
    with pytest.raises(RoomAuthorizationDenied):
        cases.open_for_process(_user(), PROCESS, authorization=BEARER)
    assert len(repo.rooms) == room_count  # no duplicate room created


# --- T-09/T-10: archive release + governed restore ---------------------------


def test_archive_releases_primary_claim_and_new_room_can_claim():
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    cases.post_message(_user(), room.id, "histórico", authorization=BEARER)
    cases.delete_room(_user(), room.id)  # owner

    assert repo.find_active_primary_room("helpdesk_ticket", TICKET) is None
    fresh = _ticket_room(cases, user=_user(user_id=OTHER))
    assert fresh.id != room.id
    link = next(l for l in repo.list_links(room.id, include_inactive=True))
    assert link.deleted_cause == "room_deleted"


def test_restore_rejects_occupied_primary_claim_without_partial_state():
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    cases.delete_room(_user(), room.id)
    fresh = _ticket_room(cases, user=_user(user_id=OTHER))

    with pytest.raises(PrimaryLinkConflict) as conflict:
        cases.restore_room(_user(), room.id, authorization=BEARER)
    assert conflict.value.error_code == "primary_link_conflict"
    # no partial reactivation: room still deleted, links still tombstoned
    raw = repo.get_raw(room.id)
    assert raw.deleted_at is not None
    assert all(not l.active for l in raw.links)


def test_restore_revives_room_deleted_links_but_not_explicit_removals():
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    ref = cases.add_link(
        _user(), room.id, "helpdesk_ticket", "9900",
        link_role="reference", authorization=BEARER,
    )
    cases.remove_link(_user(), room.id, ref.id)  # explicit — no history yet
    cases.delete_room(_user(), room.id)
    restored = cases.restore_room(_user(), room.id, authorization=BEARER)
    assert restored.deleted_at is None
    by_key = {l.entity_key: l for l in repo.list_links(room.id, include_inactive=True)}
    assert by_key[TICKET].deleted_at is None  # revived (room_deleted)
    assert by_key["9900"].deleted_cause == "explicit"  # stays tombstoned


def test_restore_requires_ticket_still_visible():
    cases, repo, tickets, _ = _cases()
    room = _ticket_room(cases)
    cases.delete_room(_user(), room.id)
    tickets.states[TICKET] = LINK_STATE_NOT_FOUND
    with pytest.raises(RoomAuthorizationDenied):
        cases.restore_room(_user(), room.id, authorization=BEARER)


def test_delete_impact_is_metadata_only():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "Título sensível", participant_ids=[OTHER])
    cases.post_message(_user(), room.id, "conteúdo")
    cases.post_message(_user(), room.id, "mais")
    impact = cases.delete_impact(_manager(), room.id)
    # 2 messages + 1 read marker created by the author's post_message
    assert impact["protected_content_count"] == 3
    assert impact["participant_count"] == 2
    assert "title" not in impact
    assert all("entity_key" not in json for json in [impact])
    # R-5: protected identifiers never surface on the public preview.
    assert "active_link_ids" not in impact
    assert "participant_user_ids" not in impact


def test_admin_room_state_is_internal_and_scoped():
    """Internal governed snapshot: owner/manage authority only, opaque
    structural ids present (fingerprint/read-back), never member-visible."""
    cases, _, _, _ = _cases()
    room = cases.open_standalone(_user(), "Sala", participant_ids=[OTHER])
    state = cases.admin_room_state(_manager(), room.id)
    assert state["deleted"] is False
    assert state["participant_count"] == 2
    assert set(state["participant_user_ids"]) == {USER, OTHER}
    # plain member without admin authority is denied
    with pytest.raises(AuthorizationDenied):
        cases.admin_room_state(_user(user_id=OTHER), room.id)
    # a manage-only admin (no content access) is allowed
    admin = _user(user_id=THIRD, permissions=[MANAGE_PERMISSION])
    assert cases.admin_room_state(admin, room.id)["room_id"] == room.id


def test_membership_active_is_own_participation_only():
    """Own-participation probe: self=True/False; querying another user's
    participation is denied — self-knowledge only."""
    cases, _, _, _ = _cases()
    room = cases.open_standalone(_user(), "Sala", participant_ids=[OTHER])
    member = _user(user_id=OTHER)
    assert cases.membership_active(member, room.id, OTHER) is True
    cases.remove_participant(_user(), room.id, user_id=OTHER)
    assert cases.membership_active(member, room.id, OTHER) is False
    # a member cannot probe someone else's participation
    with pytest.raises(PermissionError):
        cases.membership_active(member, room.id, USER)


# --- T-12/T-13: admin without access + GLPI failure modes ---------------------


def test_manage_without_access_administers_but_cannot_read():
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    cases.post_message(_user(), room.id, "restrito", authorization=BEARER)
    admin = _user(user_id=THIRD, permissions=[MANAGE_PERMISSION])

    # administration never grants content read
    with pytest.raises(AuthorizationDenied) as denied:
        cases.get_room(admin, room.id)
    assert denied.value.status_code == 403
    impact = cases.delete_impact(admin, room.id)
    assert impact["room_id"] == room.id
    deleted = cases.delete_room(admin, room.id)
    assert deleted.deleted_at is not None


@pytest.mark.parametrize(
    "state,expected_status,expected_code",
    [
        (LINK_STATE_RESTRICTED, 404, "not_found"),
        (LINK_STATE_NOT_FOUND, 404, "not_found"),
        (LINK_STATE_SESSION_MISSING, 403, "glpi_link_required"),
        (LINK_STATE_UNAVAILABLE, 503, "upstream_unavailable"),
    ],
)
def test_glpi_failure_modes_fail_closed(state, expected_status, expected_code):
    cases, repo, tickets, _ = _cases()
    room = _ticket_room(cases)
    tickets.states[TICKET] = state
    with pytest.raises(RoomAuthorizationDenied) as denied:
        cases.get_room(_user(), room.id, authorization=BEARER)
    assert denied.value.status_code == expected_status
    assert denied.value.error_code == expected_code


def test_missing_bearer_fails_closed_on_ticket_link():
    cases, _, _, _ = _cases()
    room = _ticket_room(cases)
    with pytest.raises(RoomAuthorizationDenied) as denied:
        cases.get_room(_user(), room.id, authorization=None)
    assert denied.value.error_code == "glpi_link_required"


def test_open_for_ticket_never_anchors_invisible_ticket():
    cases, repo, _, _ = _cases(default=LINK_STATE_RESTRICTED)
    with pytest.raises(RoomAuthorizationDenied):
        cases.open_for_ticket(_user(), TICKET, authorization=BEARER)
    assert repo.rooms == {}


def test_open_or_locate_existing_ticket_room_respects_members_scope():
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    cases.add_participant(_user(), room.id, OTHER)
    located = cases.open_for_ticket(_user(user_id=OTHER), TICKET, authorization=BEARER)
    assert located.id == room.id  # same canonical room — participants locate it
    # non-participant cannot locate it even with a valid ticket ACL
    with pytest.raises(RoomAuthorizationDenied):
        cases.open_for_ticket(_user(user_id=THIRD), TICKET, authorization=BEARER)


def test_open_for_ticket_race_re_resolves_to_winner():
    """A primary claim landing between the lookup and the insert makes the
    loser resolve to the canonical room instead of duplicating — the same
    path PG takes on 23505 (E1 evidence)."""
    cases, repo, _, _ = _cases()
    holder = cases.open_standalone(_user(user_id=OTHER), "vencedora")
    real_find = repo.find_active_primary_room
    calls: list[int] = []

    def racing_find(entity_type, entity_key):
        calls.append(1)
        if len(calls) == 1:
            repo.upsert_link(
                room_id=holder.id,
                entity_type=entity_type,
                entity_key=entity_key,
                link_role="primary",
                actor_user_id=OTHER,
            )
            return None
        return real_find(entity_type, entity_key)

    repo.find_active_primary_room = racing_find
    room_count = len(repo.rooms)
    # Non-participant loser: resolves to the winner and is denied — and the
    # atomic create left NO orphan room behind (rolled back as a whole).
    with pytest.raises(RoomAuthorizationDenied):
        cases.open_for_ticket(_user(user_id=THIRD), TICKET, authorization=BEARER)
    assert len(repo.rooms) == room_count
    primaries = [
        l for l in repo.links.values()
        if l.entity_key == TICKET and l.link_role == "primary" and l.deleted_at is None
    ]
    assert len(primaries) == 1
    assert primaries[0].room_id == holder.id


def test_open_for_process_denied_performs_no_writes():
    """P1: locate → authorize → mutate. An unauthorized requester on a
    multi-primary room gets denied without touching links, rooms or
    creating a duplicate."""
    cases, repo, tickets, _ = _cases()
    room = _ticket_room(cases)
    cases.add_link(
        _user(), room.id, "process", PROCESS,
        link_role="primary", authorization=BEARER,
    )
    tickets.states[TICKET] = LINK_STATE_RESTRICTED

    upserts: list[dict] = []
    real_upsert = repo.upsert_link
    repo.upsert_link = lambda **kw: (upserts.append(kw), real_upsert(**kw))[1]
    creates: list[dict] = []
    real_create = repo.create_room_graph
    repo.create_room_graph = lambda **kw: (creates.append(kw), real_create(**kw))[1]

    with pytest.raises(RoomAuthorizationDenied):
        cases.open_for_process(_user(user_id=OTHER), PROCESS, authorization=BEARER)
    assert upserts == [] and creates == []
    assert set(repo.rooms) == {room.id}


def test_open_for_process_does_not_revive_explicit_link_removal():
    """An explicitly removed primary process link stays tombstoned: a new
    open claims the object in a NEW room rather than resurrecting the
    honored removal on the old one."""
    cases, repo, _, _ = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    link = cases.add_link(
        _user(), room.id, "process", PROCESS_B, link_role="primary"
    )
    cases.remove_link(_user(), room.id, link.id)  # non-anchor: removable
    reopened = cases.open_for_process(_user(), PROCESS_B)
    assert reopened.id != room.id
    tomb = next(
        item for item in repo.list_links(room.id, include_inactive=True)
        if item.entity_type == "process" and item.entity_key == PROCESS_B
    )
    assert tomb.deleted_at is not None and tomb.deleted_cause == "explicit"


def test_anchor_process_link_removal_is_locked():
    """5.3: the primary link matching rooms.processo_id is locked — the
    legacy column would keep resolving this room while another claimed
    the primary link."""
    cases, repo, _, _ = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    anchor = repo.list_links(room.id)[0]
    with pytest.raises(RoomAnchorLinkRemovalLocked):
        cases.remove_link(_user(), room.id, anchor.id)
    assert repo.list_links(room.id)[0].active


def test_create_room_graph_rolls_back_on_occupied_primary():
    """P1 atomicity: an intermediate failure (occupied claim) leaves no
    room, link or participant rows behind."""
    cases, repo, _, _ = _cases()
    holder = cases.open_standalone(_user(user_id=OTHER), "vencedora")
    repo.upsert_link(
        room_id=holder.id,
        entity_type="helpdesk_ticket",
        entity_key=TICKET,
        link_role="primary",
        actor_user_id=OTHER,
    )
    snapshot = (set(repo.rooms), set(repo.links), set(repo.participants))
    with pytest.raises(PrimaryLinkConflict):
        repo.create_room_graph(
            title=None,
            access_scope="members",
            created_by_user_id=THIRD,
            links=(("helpdesk_ticket", TICKET, "primary"),),
            owner_participant=True,
        )
    assert (set(repo.rooms), set(repo.links), set(repo.participants)) == snapshot


def test_read_marker_counts_as_protected_history():
    """R-1 strict: any persisted artifact — even a read marker on an
    otherwise empty room — blocks restrictive link removal."""
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    cases.mark_read(_user(), room.id, authorization=BEARER)
    link = next(l for l in repo.list_links(room.id) if l.entity_type == "helpdesk_ticket")
    with pytest.raises(RoomAccessExpansionBlocked):
        cases.remove_link(_user(), room.id, link.id)


# --- P0 concurrency: R-1 TOCTOU -------------------------------------------------


def _ticket_link(repo, room_id):
    return next(
        l for l in repo.list_links(room_id) if l.entity_type == "helpdesk_ticket"
    )


def test_unguarded_sequence_demonstrates_toctou():
    """Reproduces the reviewed hazard: count → (concurrent authorized
    write) → tombstone leaves history accessible to an expanded
    audience — the exact leak the guarded op prevents."""
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    link = _ticket_link(repo, room.id)
    assert repo.protected_content_count(room.id) == 0
    # authorized writer lands between the check and the tombstone
    repo.add_message(room_id=room.id, author_user_id=USER, content="histórico")
    repo.tombstone_link(link.id, cause="explicit")
    # torn state: link gone, history exists — the bug, kept as evidence
    assert repo.links[link.id].deleted_at is not None
    assert repo.protected_content_count(room.id) == 1


def test_guarded_removal_serializes_writer_outside_critical_section():
    """Writer that arrives while the guard holds the room lock waits for
    the whole critical section — it can never slip between recount and
    tombstone."""
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    link = _ticket_link(repo, room.id)
    entered = threading.Event()
    release = threading.Event()
    real_count = repo.protected_content_count

    def slow_count(room_id):
        entered.set()
        release.wait(5)
        return real_count(room_id)

    repo.protected_content_count = slow_count
    outcome: dict = {}
    t_rem = threading.Thread(
        target=lambda: outcome.setdefault(
            "rem",
            repo.tombstone_link_guarded(
                room_id=room.id, link_id=link.id, cause="explicit"
            ),
        )
    )
    t_rem.start()
    assert entered.wait(5)
    t_w = threading.Thread(
        target=lambda: outcome.setdefault(
            "msg",
            repo.add_message(room_id=room.id, author_user_id=USER, content="x"),
        )
    )
    t_w.start()
    time.sleep(0.2)
    assert t_w.is_alive(), "writer must wait on the room lock"
    release.set()
    t_rem.join(5)
    t_w.join(5)
    # consistent ordering: tombstone committed, then writer landed
    assert outcome["rem"].deleted_at is not None
    assert outcome["msg"].id in repo.messages


def test_guarded_removal_blocked_when_writer_lands_first():
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    link = _ticket_link(repo, room.id)
    repo.add_message(room_id=room.id, author_user_id=USER, content="antes")
    with pytest.raises(RoomAccessExpansionBlocked):
        repo.tombstone_link_guarded(
            room_id=room.id, link_id=link.id, cause="explicit"
        )
    assert repo.links[link.id].deleted_at is None


def test_guarded_removal_failure_leaves_link_active():
    """An intermediate failure inside the guard mutates nothing."""
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    link = _ticket_link(repo, room.id)

    def boom(room_id):
        raise RuntimeError("storage down")

    repo.protected_content_count = boom
    with pytest.raises(RuntimeError):
        repo.tombstone_link_guarded(
            room_id=room.id, link_id=link.id, cause="explicit"
        )
    assert repo.links[link.id].deleted_at is None


def test_after_race_denied_readers_stay_denied():
    """Even after a guarded removal the room's scope still rules: a
    non-participant who lacked ticket ACL keeps getting 404."""
    cases, repo, tickets, _ = _cases()
    room = _ticket_room(cases)
    link = _ticket_link(repo, room.id)
    tickets.states[TICKET] = LINK_STATE_RESTRICTED
    repo.tombstone_link_guarded(
        room_id=room.id, link_id=link.id, cause="explicit"
    )
    with pytest.raises(RoomAuthorizationDenied) as denied:
        cases.get_room(_user(user_id=OTHER), room.id, authorization=BEARER)
    assert denied.value.status_code == 404


# --- P0 final: stale authorization rejected under the lock ---------------------------


def test_stale_write_rejected_after_link_removal():
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    link = _ticket_link(repo, room.id)
    repo.tombstone_link(link.id, cause="explicit")
    with pytest.raises(StaleRoomAuthorization):
        repo.add_message(
            room_id=room.id, author_user_id=USER, content="x",
            expected_room=room,
        )
    assert repo.protected_content_count(room.id) == 0


def test_stale_write_rejected_after_participant_removal():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "membros", participant_ids=[OTHER])
    repo.remove_participant(room_id=room.id, user_id=OTHER)
    with pytest.raises(StaleRoomAuthorization):
        repo.add_message(
            room_id=room.id, author_user_id=OTHER, content="x",
            expected_room=room,
        )


def test_stale_write_rejected_after_room_soft_delete():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "saiu")
    repo.soft_delete(room.id, actor_user_id=USER)
    with pytest.raises(StaleRoomAuthorization):
        repo.add_message(
            room_id=room.id, author_user_id=USER, content="x",
            expected_room=room,
        )


def test_stale_write_rejected_after_new_restrictive_link():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "antes")
    repo.upsert_link(
        room_id=room.id, entity_type="helpdesk_ticket",
        entity_key=TICKET, link_role="reference", actor_user_id=USER,
    )
    with pytest.raises(StaleRoomAuthorization):
        repo.add_message(
            room_id=room.id, author_user_id=USER, content="x",
            expected_room=room,
        )


def test_write_proceeds_when_context_unchanged():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "ok", participant_ids=[OTHER])
    created = repo.add_message(
        room_id=room.id, author_user_id=OTHER, content="válido",
        expected_room=room, mark_author_read=True,
    )
    assert created.id in repo.messages
    assert (room.id, OTHER) in repo.reads


def test_post_message_rejects_when_context_changes_midflight():
    """Use-case level: the authorized snapshot is revalidated under the
    lock — a mutation between authz and the write fails the whole call."""
    cases, repo, _, _ = _cases()
    room = _ticket_room(cases)
    link = _ticket_link(repo, room.id)
    original = repo.add_message

    def mutating_write(**kwargs):
        repo.tombstone_link(link.id, cause="explicit")
        return original(**kwargs)

    repo.add_message = mutating_write
    with pytest.raises(StaleRoomAuthorization):
        cases.post_message(_user(), room.id, "fora de época", authorization=BEARER)
    assert repo.protected_content_count(room.id) == 0


def test_post_message_marks_author_read_atomically():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "lido")
    cases.post_message(_user(), room.id, "oi")
    assert (room.id, USER) in repo.reads
    assert repo.protected_content_count(room.id) == 2


@pytest.mark.parametrize(
    "write",
    [
        lambda repo, room: repo.update_message(
            message_id=_first_message(repo, room.id), content="e",
            expected_room=room,
        ),
        lambda repo, room: repo.soft_delete_message(
            _first_message(repo, room.id), expected_room=room
        ),
        lambda repo, room: repo.toggle_reaction(
            message_id=_first_message(repo, room.id), user_id=USER,
            code="like", expected_room=room,
        ),
        lambda repo, room: repo.pin_message(
            room_id=room.id, message_id=_first_message(repo, room.id),
            user_id=USER, expected_room=room,
        ),
        lambda repo, room: repo.unpin_message(
            room_id=room.id, message_id=_first_message(repo, room.id),
            expected_room=room,
        ),
        lambda repo, room: repo.mark_read(
            room_id=room.id, user_id=OTHER, expected_room=room
        ),
    ],
)
def test_all_writers_reject_stale_context(write):
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "sweep", participant_ids=[OTHER])
    repo.add_message(room_id=room.id, author_user_id=USER, content="m")
    authorized = repo.get(room.id)
    repo.soft_delete(room.id, actor_user_id=USER)
    with pytest.raises(StaleRoomAuthorization):
        write(repo, authorized)


def _first_message(repo, room_id):
    return next(m.id for m in repo.messages.values() if m.room_id == room_id)


# --- actor-membership coverage: the four writers that lacked it -----------------------


def _members_room_with_message():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "cobertura", participant_ids=[OTHER])
    msg = repo.add_message(room_id=room.id, author_user_id=OTHER, content="v1")
    return repo, room, msg


def test_stale_member_cannot_edit_message():
    repo, room, msg = _members_room_with_message()
    snapshot = repo.get(room.id)
    repo.remove_participant(room_id=room.id, user_id=OTHER)
    with pytest.raises(StaleRoomAuthorization):
        repo.update_message(
            message_id=msg.id, content="v2", expected_room=snapshot,
            actor_user_id=OTHER,
        )
    assert repo.messages[msg.id].content == "v1"


def test_stale_member_cannot_delete_message():
    repo, room, msg = _members_room_with_message()
    snapshot = repo.get(room.id)
    repo.remove_participant(room_id=room.id, user_id=OTHER)
    with pytest.raises(StaleRoomAuthorization):
        repo.soft_delete_message(
            msg.id, expected_room=snapshot, actor_user_id=OTHER
        )
    assert repo.messages[msg.id].deleted_at is None


def test_stale_member_cannot_unpin():
    repo, room, msg = _members_room_with_message()
    repo.pin_message(room_id=room.id, message_id=msg.id, user_id=USER)
    snapshot = repo.get(room.id)
    repo.remove_participant(room_id=room.id, user_id=OTHER)
    with pytest.raises(StaleRoomAuthorization):
        repo.unpin_message(
            room_id=room.id, message_id=msg.id,
            expected_room=snapshot, actor_user_id=OTHER,
        )
    assert (room.id, msg.id) in repo.pins


def test_stale_member_cannot_delete_attachment():
    from tm_app.domain.entities.interaction_room import InteractionAttachment

    repo, room, msg = _members_room_with_message()
    attachment = repo.add_attachment(
        InteractionAttachment(
            id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            message_id=msg.id, room_id=room.id, file_name="doc.txt",
            content_type="text/plain", byte_size=10,
            uploaded_by_user_id=OTHER, created_at=None, stored_name="x.txt",
        )
    )
    snapshot = repo.get(room.id)
    repo.remove_participant(room_id=room.id, user_id=OTHER)
    with pytest.raises(StaleRoomAuthorization):
        repo.delete_attachment(
            attachment.id, expected_room=snapshot, actor_user_id=OTHER
        )
    assert attachment.id in repo.attachments


def test_stale_member_edit_rejected_at_use_case_level():
    """Mid-flight interleaving at the real call boundary: authz resolves,
    the removal commits, then the write hits the lock + revalidation."""
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "mid", participant_ids=[OTHER])
    msg = repo.add_message(room_id=room.id, author_user_id=OTHER, content="v1")
    original = repo.update_message

    def mutating(**kwargs):
        repo.remove_participant(room_id=room.id, user_id=OTHER)
        return original(**kwargs)

    repo.update_message = mutating
    with pytest.raises(StaleRoomAuthorization):
        cases.edit_message(_user(user_id=OTHER), room.id, msg.id, "v2")
    assert repo.messages[msg.id].content == "v1"


def test_stale_attachment_insert_leaves_no_orphan_file(tmp_path):
    """Failure after the disk save must not leave a file without a
    persisted reference."""
    from tm_app.infrastructure.storage.interaction_attachment_storage import (
        InteractionAttachmentStorage,
    )

    repo = InMemoryInteractionRoomRepository()
    cases = InteractionRoomUseCases(
        repo, storage=InteractionAttachmentStorage(str(tmp_path))
    )
    room = cases.open_standalone(_user(), "anexo", participant_ids=[OTHER])
    msg = repo.add_message(room_id=room.id, author_user_id=OTHER, content="m")
    original = repo.add_attachment

    def stale_insert(attachment, **kwargs):
        repo.remove_participant(room_id=room.id, user_id=OTHER)
        return original(attachment, **kwargs)

    repo.add_attachment = stale_insert
    with pytest.raises(StaleRoomAuthorization):
        cases.add_attachment(
            _user(user_id=OTHER), room.id, msg.id,
            file_name="doc.txt", content=b"conteudo", mime_type="text/plain",
        )
    files = [p for p in tmp_path.rglob("*") if p.is_file()]
    assert files == [], f"órfão em disco: {files}"
    assert repo.attachments == {}


# --- P1 participant self-removal ---------------------------------------------------


def test_participant_can_remove_only_themselves():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "equipe", participant_ids=[OTHER])
    cases.remove_participant(_user(user_id=OTHER), room.id, OTHER)
    assert not repo.is_participant(room.id, OTHER)
    with pytest.raises(RoomAuthorizationDenied):
        cases.get_room(_user(user_id=OTHER), room.id)
    # ...but cannot remove others
    cases.add_participant(_user(), room.id, THIRD)
    with pytest.raises(AuthorizationDenied):
        cases.remove_participant(_user(user_id=OTHER), room.id, THIRD)


def test_owner_cannot_self_remove():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "minha")
    with pytest.raises(PermissionError):
        cases.remove_participant(_user(), room.id, USER)
    assert repo.is_participant(room.id, USER)


def test_self_removal_needs_existing_participation():
    cases, _, _, _ = _cases()
    room = cases.open_standalone(_user(), "fechada")
    with pytest.raises(LookupError):
        cases.remove_participant(_user(user_id=OTHER), room.id, OTHER)


def test_audit_failure_does_not_corrupt_write_result(caplog):
    """Audit loss after a committed write is logged, never a false failure."""
    cases, repo, _, audit = _cases()
    def broken(**kwargs):
        raise RuntimeError("audit store down")
    audit.log = broken
    room = _ticket_room(cases)  # create path audits — must still succeed
    deleted = cases.delete_room(_user(), room.id)
    assert deleted.deleted_at is not None
    with pytest.raises(LookupError):
        cases.get_room(_user(), room.id)
    assert "interaction_room_audit_failed" in caplog.text


def test_http_delete_returns_safe_admin_projection():
    """P0: the DELETE route must never serialize the room entity — a
    manage-only admin deletes without seeing title, participants, history
    preview or protected link keys."""
    from tm_app.interface.http.routes import interaction_room_routes

    cases, repo, _, _ = _cases()
    room = cases.open_standalone(
        _user(), "Título Confidencial", participant_ids=[OTHER]
    )
    cases.post_message(_user(), room.id, "conteúdo restrito")
    admin_request = SimpleNamespace(
        state=SimpleNamespace(
            user=_user(user_id=THIRD, permissions=[MANAGE_PERMISSION])
        )
    )
    with patch.object(interaction_room_routes, "_rooms", cases):
        denied = interaction_room_routes.delete_interaction_room(
            SimpleNamespace(state=SimpleNamespace(user=_user(user_id=OTHER))),
            room.id,
        )
        assert denied.status_code == 403

        response = interaction_room_routes.delete_interaction_room(
            admin_request, room.id
        )
    payload = json.loads(response.body)
    assert response.status_code == 200 and payload["success"] is True
    assert payload["data"]["id"] == room.id
    assert payload["data"]["deleted_at"] is not None
    for leaked in (
        "title", "processo_nome", "processo_codigo", "participants",
        "last_message_preview", "links", "last_message_at", "processo_id",
    ):
        assert leaked not in payload["data"]
    # read-back: the room is gone for everyone
    with pytest.raises(LookupError):
        cases.get_room(_user(), room.id)


# --- standalone / participants -------------------------------------------------


def test_standalone_room_is_members_only():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "Discussão técnica", participant_ids=[OTHER])
    assert room.access_scope == "members"
    assert cases.get_room(_user(user_id=OTHER), room.id).id == room.id
    with pytest.raises(RoomAuthorizationDenied):
        cases.get_room(_user(user_id=THIRD), room.id)
    assert [item.id for item in cases.list_rooms(_user(user_id=THIRD))] == []


def test_add_link_requires_admin_not_membership():
    cases, repo, _, _ = _cases()
    room = cases.open_standalone(_user(), "Sala", participant_ids=[OTHER])
    with pytest.raises(AuthorizationDenied):
        cases.add_link(_user(user_id=OTHER), room.id, "process", PROCESS_B, link_role="reference")


def test_audit_records_lifecycle_ops():
    cases, repo, _, audit = _cases()
    room = _ticket_room(cases)
    cases.delete_room(_user(), room.id)
    cases.restore_room(_user(), room.id, authorization=BEARER)
    actions = [e["action"] for e in audit.entries]
    assert "create" in actions and "delete" in actions and "restore" in actions
    assert all(e["entity_type"] == "interaction_room" for e in audit.entries)


# --- T-15: legacy regression ---------------------------------------------------


def test_legacy_process_room_unchanged():
    cases, repo, _, _ = _cases()
    first = cases.open_for_process(_user(), PROCESS)
    second = cases.open_for_process(_user(), PROCESS)
    assert first.id == second.id
    # dual-write: primary process link materialized
    link = next(l for l in repo.list_links(first.id))
    assert (link.entity_type, link.entity_key, link.link_role) == (
        "process", PROCESS, "primary",
    )
    assert first.processo_id == PROCESS
    cases.post_message(_user(), first.id, "ok")
    assert cases.list_rooms(_user())[0].id == first.id


# --- can_view_room: typed read-authorization capability ----------------------
# The same canonical decision as _authorized_room, surfaced as a boolean for
# projections (task origin context) that must not leak room content.


def test_can_view_room_open_process_room_for_access_user():
    cases, _, _, _ = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    assert cases.can_view_room(_user(user_id=OTHER), room.id, BEARER) is True


def test_can_view_room_members_scope_requires_participation():
    cases, _, _, _ = _cases()
    room = cases.open_standalone(_user(), "War room", participant_ids=[OTHER])
    assert cases.can_view_room(_user(user_id=OTHER), room.id, BEARER) is True
    assert cases.can_view_room(_user(user_id=THIRD), room.id, BEARER) is False
    # transformometro.manage is an administrative authority, not a room read.
    assert cases.can_view_room(_manager(), room.id, BEARER) is False


def test_can_view_room_ticket_link_external_states_fail_closed():
    cases, _, tickets, _ = _cases()
    room = _ticket_room(cases)

    assert cases.can_view_room(_user(), room.id, BEARER) is True
    # Missing external session → cannot confirm visibility → closed.
    assert cases.can_view_room(_user(), room.id, None) is False
    tickets.states[TICKET] = LINK_STATE_RESTRICTED
    assert cases.can_view_room(_user(), room.id, BEARER) is False
    tickets.states[TICKET] = LINK_STATE_UNAVAILABLE
    assert cases.can_view_room(_user(), room.id, BEARER) is False


def test_can_view_room_fresh_decision_after_revocation():
    cases, _, tickets, _ = _cases()
    room = _ticket_room(cases)
    assert cases.can_view_room(_user(), room.id, BEARER) is True
    tickets.states[TICKET] = LINK_STATE_RESTRICTED
    assert cases.can_view_room(_user(), room.id, BEARER) is False
    tickets.states[TICKET] = LINK_STATE_VISIBLE
    assert cases.can_view_room(_user(), room.id, BEARER) is True


def test_can_view_room_missing_or_deleted_room_is_false():
    cases, _, _, _ = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    missing = "99999999-9999-9999-9999-999999999999"
    assert cases.can_view_room(_user(), missing, BEARER) is False
    cases.delete_room(_user(), room.id)
    assert cases.can_view_room(_user(), room.id, BEARER) is False


def test_can_view_room_requires_access_permission():
    cases, _, _, _ = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    outsider = _user(user_id=THIRD, permissions=[])
    assert cases.can_view_room(outsider, room.id, BEARER) is False


def test_can_view_room_v1_schema_reduces_to_existence():
    """Legacy schema: no access_scope/links/participants — the model carries
    no restrictive contract, so the canonical decision is room existence +
    transformometro.access. Never a bypass: those checks simply do not exist."""
    cases, repo, _, _ = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    repo.room_schema_v2 = lambda: False
    assert cases.can_view_room(_user(user_id=THIRD), room.id, None) is True
    repo.rooms.pop(room.id)
    assert cases.can_view_room(_user(user_id=THIRD), room.id, None) is False
    outsider = _user(user_id=THIRD, permissions=[])
    assert cases.can_view_room(outsider, "99999999-9999-9999-9999-999999999999", None) is False
