"""E3 — real routing tests for the Interaction Rooms V2 HTTP surface.

Uses FastAPI TestClient with an auth middleware stub honoring the same
contract as ``delpi_auth`` (``request.state.user`` populated → request
runs; absent → 401). Use cases are backed by the InMemory repository
and a FakeTicketVisibility double — routing, envelopes, status codes and
DTO validation are real; Keycloak/GLPI integration is TEST_NOT_RUN.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from tm_app.application.security.authorization_policy import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
)
from tm_app.application.use_cases.manage_interaction_rooms import InteractionRoomUseCases
from tm_app.domain.services.interaction_room_access_service import (
    LINK_STATE_RESTRICTED,
    LINK_STATE_UNAVAILABLE,
    LINK_STATE_VISIBLE,
)
from tm_app.infrastructure.persistence.repositories.interaction_room_repository import (
    InMemoryInteractionRoomRepository,
)
from tm_app.interface.http.routes import interaction_room_routes

USER = "11111111-1111-1111-1111-111111111111"
OTHER = "22222222-2222-2222-2222-222222222222"
THIRD = "66666666-6666-6666-6666-666666666666"
PROCESS = "33333333-3333-3333-3333-333333333333"
PROCESS_B = "44444444-4444-4444-4444-444444444444"
TICKET = "1275"
BEARER = "Bearer test-token"

BASE = "/transformometro/interaction-rooms"


class FakeTicketVisibility:
    def __init__(self, states: dict[str, str] | None = None, default: str = LINK_STATE_VISIBLE):
        self.states = states or {}
        self.default = default
        self.calls: list[tuple[str | None, str]] = []

    def check_ticket_visibility(self, authorization: str, ticket_key: str) -> str:
        self.calls.append((authorization, ticket_key))
        if not authorization:
            return "session_missing"
        return self.states.get(ticket_key, self.default)


def _make_client():
    """Fresh app+client per call: InMemory repo, fake tickets, stub auth.

    Auth headers: ``x-test-user`` (id), ``x-test-perms`` (csv, default
    'access'). Missing ``x-test-user`` → 401 like the real middleware."""
    repo = InMemoryInteractionRoomRepository()
    repo.processes.update({PROCESS, PROCESS_B})
    tickets = FakeTicketVisibility()
    cases = InteractionRoomUseCases(repo, ticket_visibility=tickets)
    app = FastAPI()

    @app.middleware("http")
    async def _auth_stub(request: Request, call_next):
        user_id = request.headers.get("x-test-user")
        if not user_id:
            return JSONResponse(
                {"success": False, "message": "unauthenticated", "data": None},
                status_code=401,
            )
        perms = request.headers.get("x-test-perms", ACCESS_PERMISSION).split(",")
        request.state.user = SimpleNamespace(
            id=user_id,
            permissions=[p for p in perms if p],
            is_superadmin=False,
        )
        return await call_next(request)

    app.include_router(interaction_room_routes.router)
    with patch.object(interaction_room_routes, "_rooms", cases):
        yield TestClient(app), repo, tickets


@pytest.fixture()
def env():
    yield from _make_client()


def _headers(user_id: str = USER, *perms: str, bearer: bool = True):
    headers = {"x-test-user": user_id}
    if perms:
        headers["x-test-perms"] = ",".join(perms)
    if bearer:
        headers["authorization"] = BEARER
    return headers


def _data(resp):
    body = resp.json()
    assert body["success"] is True
    return body["data"]


# --- authN / middleware --------------------------------------------------------


def test_unauthenticated_request_returns_401(env):
    client, _, _ = env
    resp = client.get(BASE)
    assert resp.status_code == 401
    assert resp.json()["success"] is False


def test_invalid_dto_returns_422(env):
    client, _, _ = env
    resp = client.post(f"{BASE}/ticket", json={}, headers=_headers())
    assert resp.status_code == 422


# --- open / locate ---------------------------------------------------------------


def test_open_process_room_roundtrip_and_idempotent(env):
    client, repo, _ = env
    resp = client.post(BASE, json={"processo_id": PROCESS}, headers=_headers())
    assert resp.status_code == 200
    room = _data(resp)
    assert room["processo_id"] == PROCESS
    assert len(repo.rooms) == 1

    again = client.post(BASE, json={"processo_id": PROCESS}, headers=_headers())
    assert _data(again)["id"] == room["id"]
    assert len(repo.rooms) == 1
    # authoritative read-back: primary process link persisted
    links = [l for l in repo.links.values() if l.room_id == room["id"]]
    assert any(
        l.entity_type == "process" and l.entity_key == PROCESS
        and l.link_role == "primary" and l.deleted_at is None
        for l in links
    )


def test_open_process_room_not_found(env):
    client, _, _ = env
    resp = client.post(
        BASE, json={"processo_id": "99999999-9999-9999-9999-999999999999"},
        headers=_headers(),
    )
    assert resp.status_code == 404


def test_open_ticket_room_forwards_user_bearer(env):
    client, _, tickets = env
    resp = client.post(
        f"{BASE}/ticket", json={"ticket_id": TICKET}, headers=_headers()
    )
    assert resp.status_code == 200
    room = _data(resp)
    assert room["access_scope"] == "members"
    # the user's Bearer — never a service token — reached the authority
    assert tickets.calls and tickets.calls[0][0] == BEARER


def test_open_ticket_room_denied_without_acl_hides_existence(env):
    client, _, tickets = env
    tickets.states[TICKET] = LINK_STATE_RESTRICTED
    resp = client.post(
        f"{BASE}/ticket", json={"ticket_id": TICKET}, headers=_headers()
    )
    assert resp.status_code == 404
    assert resp.json()["data"]["error_code"] == "not_found"


def test_open_ticket_room_glpi_down_is_503_fail_closed(env):
    client, _, tickets = env
    tickets.states[TICKET] = LINK_STATE_UNAVAILABLE
    resp = client.post(
        f"{BASE}/ticket", json={"ticket_id": TICKET}, headers=_headers()
    )
    assert resp.status_code == 503
    assert resp.json()["data"]["error_code"] == "upstream_unavailable"


def test_open_ticket_room_without_bearer_requires_glpi_session(env):
    client, _, _ = env
    resp = client.post(
        f"{BASE}/ticket",
        json={"ticket_id": TICKET},
        headers={"x-test-user": USER, "x-test-perms": ACCESS_PERMISSION},
    )
    assert resp.status_code == 403
    assert resp.json()["data"]["error_code"] == "glpi_link_required"


def test_create_standalone_room_members_only(env):
    client, repo, _ = env
    resp = client.post(
        f"{BASE}/standalone",
        json={"title": "Discussão arquitetura", "participant_ids": [OTHER]},
        headers=_headers(),
    )
    assert resp.status_code == 201
    room = _data(resp)
    assert room["access_scope"] == "members"
    assert room["processo_id"] is None
    owner = next(
        p for p in repo.participants.values() if p.room_id == room["id"] and p.user_id == USER
    )
    assert owner.role == "owner"


# --- authorization / no existence oracle ------------------------------------------


def test_non_participant_get_denied_without_existence_leak(env):
    client, _, _ = env
    room = _data(
        client.post(
            f"{BASE}/standalone", json={"title": "Privada"}, headers=_headers()
        )
    )
    resp = client.get(f"{BASE}/{room['id']}", headers=_headers(THIRD))
    assert resp.status_code == 404
    assert resp.json()["data"]["error_code"] == "not_found"


def test_multi_primary_room_denies_when_ticket_acl_missing(env):
    """Process-linked room ALSO primary for a ticket: a requester with
    process access but no ticket ACL gets 404 — and no state changes."""
    client, repo, tickets = env
    room = _data(client.post(BASE, json={"processo_id": PROCESS}, headers=_headers()))
    client.post(
        f"{BASE}/{room['id']}/links",
        json={"entity_type": "helpdesk_ticket", "entity_key": TICKET, "link_role": "primary"},
        headers=_headers(),
    )
    tickets.states[TICKET] = LINK_STATE_RESTRICTED

    snapshot = (set(repo.rooms), set(repo.links))
    resp = client.post(BASE, json={"processo_id": PROCESS}, headers=_headers(THIRD))
    assert resp.status_code == 404
    assert (set(repo.rooms), set(repo.links)) == snapshot


def test_reference_link_restricts_reads(env):
    client, _, tickets = env
    room = _data(client.post(BASE, json={"processo_id": PROCESS}, headers=_headers()))
    resp = client.post(
        f"{BASE}/{room['id']}/links",
        json={"entity_type": "helpdesk_ticket", "entity_key": TICKET},
        headers=_headers(),
    )
    assert resp.status_code == 201
    tickets.states[TICKET] = LINK_STATE_RESTRICTED
    assert client.get(f"{BASE}/{room['id']}", headers=_headers()).status_code == 404


# --- links ------------------------------------------------------------------------


def test_add_and_remove_process_reference_link(env):
    client, repo, _ = env
    room = _data(client.post(BASE, json={"processo_id": PROCESS}, headers=_headers()))
    resp = client.post(
        f"{BASE}/{room['id']}/links",
        json={"entity_type": "process", "entity_key": PROCESS_B, "link_role": "reference"},
        headers=_headers(),
    )
    assert resp.status_code == 201
    link_id = _data(resp)["id"]
    # non-admin cannot remove
    denied = client.delete(
        f"{BASE}/{room['id']}/links/{link_id}", headers=_headers(THIRD)
    )
    assert denied.status_code == 403
    ok_resp = client.delete(f"{BASE}/{room['id']}/links/{link_id}", headers=_headers())
    assert _data(ok_resp) == {"id": link_id}


def test_legacy_process_anchor_removal_is_locked(env):
    """5.3: primary process link matching rooms.processo_id cannot be
    removed — the legacy column would keep resolving this room while a
    second room claimed the primary link."""
    client, repo, _ = env
    room = _data(client.post(BASE, json={"processo_id": PROCESS}, headers=_headers()))
    anchor = next(
        l for l in repo.links.values()
        if l.room_id == room["id"] and l.entity_key == PROCESS
    )
    resp = client.delete(
        f"{BASE}/{room['id']}/links/{anchor.id}", headers=_headers()
    )
    assert resp.status_code == 409
    assert resp.json()["data"]["error_code"] == "legacy_anchor_locked"
    assert repo.links[anchor.id].deleted_at is None


def test_remove_restrictive_link_with_history_blocked(env):
    client, _, _ = env
    room = _data(
        client.post(f"{BASE}/ticket", json={"ticket_id": TICKET}, headers=_headers())
    )
    client.post(
        f"{BASE}/{room['id']}/messages",
        json={"content": "histórico protegido"},
        headers=_headers(),
    )
    links = client.get(f"{BASE}/{room['id']}/links", headers=_headers())
    link_id = _data(links)["items"][0]["id"]
    resp = client.delete(f"{BASE}/{room['id']}/links/{link_id}", headers=_headers())
    assert resp.status_code == 409
    assert resp.json()["data"]["error_code"] == "room_access_expansion_blocked"


def test_links_listing_requires_content_authorization(env):
    client, _, _ = env
    room = _data(
        client.post(f"{BASE}/standalone", json={"title": "X"}, headers=_headers())
    )
    resp = client.get(f"{BASE}/{room['id']}/links", headers=_headers(THIRD))
    assert resp.status_code == 404


def test_duplicate_primary_claim_returns_409(env):
    client, _, _ = env
    first = _data(
        client.post(f"{BASE}/ticket", json={"ticket_id": TICKET}, headers=_headers())
    )
    second = _data(
        client.post(
            f"{BASE}/standalone", json={"title": "Y"}, headers=_headers(OTHER)
        )
    )
    resp = client.post(
        f"{BASE}/{second['id']}/links",
        json={"entity_type": "helpdesk_ticket", "entity_key": TICKET, "link_role": "primary"},
        headers=_headers(OTHER),
    )
    assert resp.status_code == 409
    assert resp.json()["data"]["error_code"] == "primary_link_conflict"
    assert first["id"] != second["id"]


# --- participants -------------------------------------------------------------------


def test_participant_lifecycle_over_http(env):
    client, _, _ = env
    room = _data(
        client.post(f"{BASE}/standalone", json={"title": "Equipe"}, headers=_headers())
    )
    resp = client.post(
        f"{BASE}/{room['id']}/participants",
        json={"user_id": OTHER},
        headers=_headers(),
    )
    assert resp.status_code == 201
    items = _data(client.get(f"{BASE}/{room['id']}/participants", headers=_headers()))["items"]
    assert {p["user_id"] for p in items} == {USER, OTHER}

    resp = client.delete(
        f"{BASE}/{room['id']}/participants/{OTHER}", headers=_headers()
    )
    assert resp.status_code == 200
    # removed participant loses the room immediately
    assert client.get(f"{BASE}/{room['id']}", headers=_headers(OTHER)).status_code == 404


def test_owner_participant_cannot_be_removed(env):
    client, _, _ = env
    room = _data(
        client.post(f"{BASE}/standalone", json={"title": "Z"}, headers=_headers())
    )
    resp = client.delete(
        f"{BASE}/{room['id']}/participants/{USER}", headers=_headers()
    )
    assert resp.status_code == 403


def test_participant_self_removal_over_http(env):
    """P1: a participant may leave — only themselves; access ends
    immediately (read-back proves it)."""
    client, _, _ = env
    room = _data(
        client.post(
            f"{BASE}/standalone",
            json={"title": "sair", "participant_ids": [OTHER]},
            headers=_headers(),
        )
    )
    resp = client.delete(
        f"{BASE}/{room['id']}/participants/{OTHER}", headers=_headers(OTHER)
    )
    assert resp.status_code == 200
    assert client.get(f"{BASE}/{room['id']}", headers=_headers(OTHER)).status_code == 404


def test_owner_self_removal_is_denied(env):
    client, _, _ = env
    room = _data(
        client.post(f"{BASE}/standalone", json={"title": "own"}, headers=_headers())
    )
    resp = client.delete(
        f"{BASE}/{room['id']}/participants/{USER}", headers=_headers()
    )
    assert resp.status_code == 403


def test_non_admin_cannot_remove_other_participant(env):
    client, _, _ = env
    room = _data(
        client.post(
            f"{BASE}/standalone",
            json={"title": "x", "participant_ids": [OTHER, THIRD]},
            headers=_headers(),
        )
    )
    resp = client.delete(
        f"{BASE}/{room['id']}/participants/{THIRD}", headers=_headers(OTHER)
    )
    assert resp.status_code == 403


def test_participant_write_requires_admin(env):
    client, _, _ = env
    room = _data(
        client.post(f"{BASE}/standalone", json={"title": "W"}, headers=_headers())
    )
    resp = client.post(
        f"{BASE}/{room['id']}/participants",
        json={"user_id": THIRD},
        headers=_headers(OTHER),
    )
    assert resp.status_code == 403


# --- admin: impact / delete / restore -----------------------------------------------


def test_delete_impact_is_metadata_only_for_manage_only_admin(env):
    client, _, _ = env
    room = _data(
        client.post(f"{BASE}/standalone", json={"title": "Segredo"}, headers=_headers())
    )
    resp = client.get(
        f"{BASE}/{room['id']}/impact",
        headers=_headers(THIRD, MANAGE_PERMISSION),
    )
    assert resp.status_code == 200
    data = _data(resp)
    for leaked in ("title", "processo_nome", "processo_codigo", "participants"):
        assert leaked not in data
    assert data["room_id"] == room["id"]
    assert "protected_content_count" in data


def test_manage_without_access_deletes_with_minimal_projection(env):
    client, _, _ = env
    room = _data(
        client.post(f"{BASE}/standalone", json={"title": "Confidencial"}, headers=_headers())
    )
    resp = client.delete(
        f"{BASE}/{room['id']}",
        headers=_headers(THIRD, MANAGE_PERMISSION),
    )
    assert resp.status_code == 200
    data = _data(resp)
    assert set(data) == {"id", "deleted_at"}
    assert data["deleted_at"] is not None
    # content routes stay closed for the admin — `transformometro.access`
    # is checked before room existence, so the denial is a clean 403
    assert (
        client.get(f"{BASE}/{room['id']}", headers=_headers(THIRD, MANAGE_PERMISSION)).status_code
        == 403
    )


def test_owner_without_manage_deletes_and_readback_gone(env):
    client, _, _ = env
    room = _data(client.post(BASE, json={"processo_id": PROCESS}, headers=_headers()))
    resp = client.delete(f"{BASE}/{room['id']}", headers=_headers())
    assert resp.status_code == 200
    assert client.get(f"{BASE}/{room['id']}", headers=_headers()).status_code == 404


def test_restore_conflict_returns_409_without_partial_state(env):
    client, repo, _ = env
    first = _data(client.post(BASE, json={"processo_id": PROCESS}, headers=_headers()))
    client.delete(f"{BASE}/{first['id']}", headers=_headers())
    second = _data(client.post(BASE, json={"processo_id": PROCESS}, headers=_headers()))
    resp = client.post(f"{BASE}/{first['id']}/restore", headers=_headers())
    assert resp.status_code == 409
    assert resp.json()["data"]["error_code"] == "primary_link_conflict"
    # nothing partially revived
    assert repo.rooms[first["id"]].deleted_at is not None
    assert not any(
        l.room_id == first["id"] and l.deleted_at is None for l in repo.links.values()
    )


def test_restore_success_minimal_projection(env):
    client, repo, _ = env
    room = _data(client.post(BASE, json={"processo_id": PROCESS}, headers=_headers()))
    client.delete(f"{BASE}/{room['id']}", headers=_headers())
    resp = client.post(f"{BASE}/{room['id']}/restore", headers=_headers())
    assert resp.status_code == 200
    assert _data(resp) == {"id": room["id"], "deleted_at": None}
    assert repo.rooms[room["id"]].deleted_at is None


def test_admin_ops_on_nonexistent_room_are_404(env):
    client, _, _ = env
    missing = "55555555-5555-5555-5555-555555555555"
    assert client.get(f"{BASE}/{missing}/impact", headers=_headers(THIRD, MANAGE_PERMISSION)).status_code == 404
    assert client.delete(f"{BASE}/{missing}", headers=_headers(THIRD, MANAGE_PERMISSION)).status_code == 404
    assert client.post(f"{BASE}/{missing}/restore", headers=_headers(THIRD, MANAGE_PERMISSION)).status_code == 404
