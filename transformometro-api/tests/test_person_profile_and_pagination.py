"""E2 — person-profile facade + list_messages before_id pagination."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tm_app.application.security.transformometro_permissions import ACCESS_PERMISSION
from tm_app.application.use_cases.manage_interaction_rooms import InteractionRoomUseCases
from tm_app.infrastructure.gateways.core_person_profile_s2s_gateway import (
    CorePersonProfileS2SGateway,
)
from tm_app.infrastructure.persistence.repositories.interaction_room_repository import (
    InMemoryInteractionRoomRepository,
)
from tm_app.interface.http.routes import interaction_room_routes, person_profile_routes

USER = "11111111-1111-1111-1111-111111111111"
PROCESS = "33333333-3333-3333-3333-333333333333"
OTHER_USER = "22222222-2222-2222-2222-222222222222"
MISSING_MSG = "55555555-5555-5555-5555-555555555555"


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


def test_person_profile_routes_exist_and_require_access():
    request = SimpleNamespace(state=SimpleNamespace(user=_user()))
    denied = person_profile_routes.list_person_profile_photo_flags(
        SimpleNamespace(state=SimpleNamespace(user=_user(permissions=[]))),
        ids=OTHER_USER,
    )
    assert denied.status_code == 403

    with patch.object(
        person_profile_routes,
        "_gateway",
        SimpleNamespace(
            lookup_has_photo=lambda ids: {OTHER_USER: True},
            get_photo_bytes=lambda uid: (b"img", "image/png", "photo.png"),
        ),
    ):
        flags = person_profile_routes.list_person_profile_photo_flags(
            request,
            ids=f"{OTHER_USER},{USER}",
        )
        photo = person_profile_routes.get_person_profile_photo(request, OTHER_USER)

    assert flags.status_code == 200
    payload = json.loads(flags.body)["data"]
    assert payload["items"] == [
        {"user_id": OTHER_USER, "has_photo": True},
        {"user_id": USER, "has_photo": False},
    ]
    assert photo.status_code == 200
    assert photo.body == b"img"
    assert photo.media_type == "image/png"


def test_person_profile_soft_fail_when_core_unavailable():
    gateway = CorePersonProfileS2SGateway(core_api_url="", service_token="")
    assert gateway.configured() is False
    assert gateway.lookup_has_photo([OTHER_USER]) == {}
    assert gateway.get_photo_bytes(OTHER_USER) is None

    request = SimpleNamespace(state=SimpleNamespace(user=_user()))
    with patch.object(person_profile_routes, "_gateway", gateway):
        flags = person_profile_routes.list_person_profile_photo_flags(
            request,
            ids=OTHER_USER,
        )
        photo = person_profile_routes.get_person_profile_photo(request, OTHER_USER)

    assert flags.status_code == 200
    assert json.loads(flags.body)["data"]["items"] == [
        {"user_id": OTHER_USER, "has_photo": False},
    ]
    assert photo.status_code == 404


def test_before_id_positive_loads_older_page():
    cases, _repo = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    first = cases.post_message(_user(), room.id, "m1")
    second = cases.post_message(_user(), room.id, "m2")
    third = cases.post_message(_user(), room.id, "m3")

    older = cases.list_messages(_user(), room.id, limit=1, before_id=third.id)
    assert [item["content"] for item in older["items"]] == ["m2"]
    assert older["has_more"] is True

    oldest = cases.list_messages(_user(), room.id, limit=2, before_id=second.id)
    assert [item["content"] for item in oldest["items"]] == ["m1"]
    assert oldest["has_more"] is False
    assert first.id == oldest["items"][0]["id"]


def test_before_id_sibling_without_cursor_returns_latest():
    cases, _repo = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    cases.post_message(_user(), room.id, "m1")
    cases.post_message(_user(), room.id, "m2")
    cases.post_message(_user(), room.id, "m3")

    latest = cases.list_messages(_user(), room.id, limit=2)
    assert [item["content"] for item in latest["items"]] == ["m2", "m3"]
    assert latest["has_more"] is True


def test_before_id_negative_invalid_and_missing():
    cases, _repo = _cases()
    room = cases.open_for_process(_user(), PROCESS)
    cases.post_message(_user(), room.id, "m1")

    with pytest.raises(ValueError):
        cases.list_messages(_user(), room.id, before_id="not-a-uuid")

    with pytest.raises(LookupError):
        cases.list_messages(_user(), room.id, before_id=MISSING_MSG)

    request = SimpleNamespace(state=SimpleNamespace(user=_user()))
    with patch.object(interaction_room_routes, "_rooms", cases):
        bad = interaction_room_routes.list_interaction_messages(
            request,
            room.id,
            before_id="not-a-uuid",
        )
        missing = interaction_room_routes.list_interaction_messages(
            request,
            room.id,
            before_id=MISSING_MSG,
        )
        ok_page = interaction_room_routes.list_interaction_messages(
            request,
            room.id,
            limit=10,
        )

    assert bad.status_code == 400
    assert missing.status_code == 404
    assert ok_page.status_code == 200
    assert "has_more" in json.loads(ok_page.body)["data"]
