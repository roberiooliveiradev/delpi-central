from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from starlette.requests import Request

from commercial_app.domain.entities.interaction_room import InteractionRoomMember
from commercial_app.interface.http.routes import interaction_room_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "user-room-test"):
        self.permissions = permissions
        self.sub = sub


def _request(path: str, method: str = "GET") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def _member() -> InteractionRoomMember:
    return InteractionRoomMember(
        id=uuid4(),
        room_id=UUID("00000000-0000-0000-0000-000000000111"),
        user_id="user-room-test",
        role="member",
        created_at=datetime.now(timezone.utc),
        last_read_at=datetime.now(timezone.utc),
    )


def test_list_members_403_without_access() -> None:
    request = _request("/interaction-rooms/x/members")
    request.state.user = _User([])
    response = interaction_room_routes.list_interaction_room_members(
        request,
        room_id=uuid4(),
    )
    assert response.status_code == 403


def test_mark_read_200(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/interaction-rooms/x/read", method="POST")
    request.state.user = _User(["commercial.access"])
    member = _member()
    fake_uc = MagicMock()
    fake_uc.mark_read.return_value = member
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_rooms_use_case",
        lambda: fake_uc,
    )
    response = interaction_room_routes.mark_interaction_room_read(
        request,
        room_id=member.room_id,
    )
    assert response.status_code == 200
    assert b"mark_interaction_room_read" in response.body


def test_add_member_201(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/interaction-rooms/x/members", method="POST")
    request.state.user = _User(["commercial.access"])
    member = _member()
    fake_uc = MagicMock()
    fake_uc.add_member.return_value = member
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_rooms_use_case",
        lambda: fake_uc,
    )
    body = SimpleNamespace(user_id="u2", role="member")
    response = interaction_room_routes.add_interaction_room_member(
        request,
        room_id=member.room_id,
        body=body,
    )
    assert response.status_code == 201
    assert b"add_interaction_room_member" in response.body


def test_remove_member_200(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/interaction-rooms/x/members/u2", method="DELETE")
    request.state.user = _User(["commercial.access"])
    fake_uc = MagicMock()
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_rooms_use_case",
        lambda: fake_uc,
    )
    room_id = uuid4()
    response = interaction_room_routes.remove_interaction_room_member(
        request,
        room_id=room_id,
        user_id="u2",
    )
    assert response.status_code == 200
    assert b"remove_interaction_room_member" in response.body
    fake_uc.remove_member.assert_called_once()
