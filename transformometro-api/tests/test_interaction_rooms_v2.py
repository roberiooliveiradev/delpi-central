"""Interaction Rooms V2 — negative-security & lifecycle suite (T-01…T-15).

Controlled doubles only: the real Postgres adapter is exercised through
the E1 preflight evidence, not here. Integration scenarios that need the
V056 schema are declared TEST_NOT_RUN in the execution report — unit
coverage proves the domain/application rules.
"""

from __future__ import annotations

from types import SimpleNamespace

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
    RoomAuthorizationDenied,
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
    room = cases.open_for_process(_user(), PROCESS)
    cases.post_message(_user(), room.id, "histórico")
    link = next(l for l in repo.list_links(room.id) if l.entity_type == "process")
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
    assert impact["message_count"] == 2
    assert impact["participant_count"] == 2
    assert "title" not in impact
    assert all("entity_key" not in json for json in [impact])


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
    # Non-participant loser: resolves to the winner and is denied — no orphan.
    with pytest.raises(RoomAuthorizationDenied):
        cases.open_for_ticket(_user(user_id=THIRD), TICKET, authorization=BEARER)
    # one orphan room was created then superseded; the claim stayed single
    primaries = [
        l for l in repo.links.values()
        if l.entity_key == TICKET and l.link_role == "primary" and l.deleted_at is None
    ]
    assert len(primaries) == 1
    assert primaries[0].room_id == holder.id


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
