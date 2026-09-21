from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from tm_app.application.security.authorization_policy import AuthorizationDenied
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
)
from tm_app.application.use_cases.manage_interaction_rooms import InteractionRoomUseCases
from tm_app.domain.services.interaction_room_rules import (
    MAX_MESSAGE_LENGTH,
    normalize_message_content,
    normalize_processo_id,
)
from tm_app.infrastructure.persistence.repositories.interaction_room_repository import (
    InMemoryInteractionRoomRepository,
)

USER = "11111111-1111-1111-1111-111111111111"
PROCESS = "33333333-3333-3333-3333-333333333333"
OTHER_PROCESS = "44444444-4444-4444-4444-444444444444"

# operationIds do baseline: list_transformometro_interaction_rooms
# open_transformometro_interaction_room
# get_transformometro_interaction_room
# list_transformometro_interaction_messages
# post_transformometro_interaction_message


def _user(*, permissions=None, user_id=USER):
    return SimpleNamespace(
        id=user_id,
        permissions=[ACCESS_PERMISSION] if permissions is None else permissions,
        is_superadmin=False,
    )


def _cases() -> tuple[InteractionRoomUseCases, InMemoryInteractionRoomRepository]:
    repo = InMemoryInteractionRoomRepository()
    repo.processes.add(PROCESS)
    return InteractionRoomUseCases(repo), repo


def test_message_rules_reject_blank_and_oversize():
    with pytest.raises(ValueError):
        normalize_message_content("   \n  ")
    with pytest.raises(ValueError):
        normalize_message_content("a" * (MAX_MESSAGE_LENGTH + 1))
    kept = normalize_message_content("  linha\n\nseguinte  ")
    assert kept == "linha\n\nseguinte"
    assert normalize_processo_id(PROCESS) == PROCESS
    with pytest.raises(ValueError):
        normalize_processo_id("nao-uuid")


def test_one_room_per_process_and_missing_context():
    cases, _repo = _cases()
    first = cases.open_for_process(_user(), PROCESS)
    second = cases.open_for_process(_user(), PROCESS)
    assert first.id == second.id
    assert first.processo_id == PROCESS
    with pytest.raises(LookupError):
        cases.open_for_process(_user(), OTHER_PROCESS)


def test_post_then_list_is_authoritative_and_ordered():
    cases, _repo = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    first = cases.post_message(_user(), room.id, "primeira")
    second = cases.post_message(_user(), room.id, "segunda")
    listed = cases.list_messages(_user(), room.id, limit=50)
    assert [item["id"] for item in listed["items"]] == [first.id, second.id]
    assert listed["items"][0]["author_user_id"] == USER
    assert listed["items"][0]["content"] == "primeira"
    assert listed["has_more"] is False
    page = cases.list_messages(_user(), room.id, limit=1)
    assert [item["content"] for item in page["items"]] == ["segunda"]
    assert page["has_more"] is True
    with pytest.raises(LookupError):
        cases.get_room(_user(), "55555555-5555-5555-5555-555555555555")


def test_authz_access_manage_and_anonymous():
    cases, _repo = _cases()
    cases.open_for_process(_user(), PROCESS)
    with pytest.raises(AuthorizationDenied) as missing:
        cases.list_rooms(_user(permissions=[]))
    assert missing.value.status_code == 403
    with pytest.raises(AuthorizationDenied) as manage_only:
        cases.post_message(_user(permissions=[MANAGE_PERMISSION]), "x", "oi")
    assert manage_only.value.status_code == 403
    with pytest.raises(AuthorizationDenied) as anonymous:
        cases.list_rooms(None)
    assert anonymous.value.status_code == 401


def test_http_read_back_and_validation():
    from tm_app.interface.http.routes import interaction_room_routes

    cases, _repo = _cases()
    request = SimpleNamespace(state=SimpleNamespace(user=_user()))
    with patch.object(interaction_room_routes, "_rooms", cases):
        opened = interaction_room_routes.open_interaction_room(
            request,
            interaction_room_routes.OpenInteractionRoomBody(processo_id=PROCESS),
        )
        missing = interaction_room_routes.open_interaction_room(
            request,
            interaction_room_routes.OpenInteractionRoomBody(processo_id=OTHER_PROCESS),
        )
        forbidden = interaction_room_routes.list_interaction_rooms(
            SimpleNamespace(state=SimpleNamespace(user=_user(permissions=[]))),
        )
        manage_only = interaction_room_routes.list_interaction_rooms(
            SimpleNamespace(state=SimpleNamespace(user=_user(permissions=[MANAGE_PERMISSION]))),
        )
        anonymous = interaction_room_routes.list_interaction_rooms(
            SimpleNamespace(state=SimpleNamespace(user=None)),
        )
        room_id = json.loads(opened.body)["data"]["id"]
        posted = interaction_room_routes.post_interaction_message(
            request,
            room_id,
            interaction_room_routes.PostInteractionMessageBody(content="  texto da sala  "),
        )
        listed = interaction_room_routes.list_interaction_messages(request, room_id)
        unknown = interaction_room_routes.get_interaction_room(
            request,
            "55555555-5555-5555-5555-555555555555",
        )
    assert opened.status_code == 200
    assert missing.status_code == 404
    assert forbidden.status_code == 403
    assert manage_only.status_code == 403
    assert anonymous.status_code == 401
    assert posted.status_code == 201
    listed_body = json.loads(listed.body)
    assert listed_body["data"]["items"][0]["content"] == "texto da sala"
    assert listed_body["data"]["items"][0]["author_user_id"] == USER
    assert unknown.status_code == 404
    with pytest.raises(ValidationError):
        interaction_room_routes.PostInteractionMessageBody(content="   ")
