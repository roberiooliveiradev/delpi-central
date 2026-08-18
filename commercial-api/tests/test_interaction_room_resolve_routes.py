from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from starlette.requests import Request

from commercial_app.domain.entities.interaction_room import InteractionRoom
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


def _sample_room() -> InteractionRoom:
    now = datetime.now(timezone.utc)
    return InteractionRoom(
        id=UUID("00000000-0000-0000-0000-000000000111"),
        kind="entity",
        title="Pedido 1",
        created_by_user_id="user-room-test",
        created_at=now,
        updated_at=now,
        entity_type="order",
        entity_key="01|1",
    )


def test_resolve_403_without_access() -> None:
    request = _request("/interaction-rooms/resolve", method="POST")
    request.state.user = _User([])
    body = SimpleNamespace(
        kind="entity",
        entity_type="order",
        entity_key="01|1",
        group_id=None,
        title=None,
    )
    response = interaction_room_routes.resolve_interaction_room(request, body)
    assert response.status_code == 403


def test_get_403_without_access() -> None:
    request = _request("/interaction-rooms/x")
    request.state.user = _User(["commercial.billing.notify"])
    response = interaction_room_routes.get_interaction_room(
        request,
        room_id=uuid4(),
    )
    assert response.status_code == 403


def test_resolve_401_without_user() -> None:
    request = _request("/interaction-rooms/resolve", method="POST")
    body = SimpleNamespace(
        kind="entity",
        entity_type="order",
        entity_key="01|1",
        group_id=None,
        title=None,
    )
    response = interaction_room_routes.resolve_interaction_room(request, body)
    assert response.status_code == 401


def test_resolve_200_with_access(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/interaction-rooms/resolve", method="POST")
    request.state.user = _User(["commercial.access"])
    room = _sample_room()
    fake_uc = MagicMock()
    fake_uc.resolve.return_value = room
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_rooms_use_case",
        lambda: fake_uc,
    )
    body = SimpleNamespace(
        kind="entity",
        entity_type="order",
        entity_key="01|1",
        group_id=None,
        title="Pedido 1",
    )
    response = interaction_room_routes.resolve_interaction_room(request, body)
    assert response.status_code == 200
    payload = response.body
    assert b"resolve_interaction_room" in payload
    assert b"00000000-0000-0000-0000-000000000111" in payload


def test_get_200_with_meta_operation_id(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/interaction-rooms/00000000-0000-0000-0000-000000000111")
    request.state.user = _User(["commercial.access"])
    room = _sample_room()
    fake_uc = MagicMock()
    fake_uc.get.return_value = room
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_rooms_use_case",
        lambda: fake_uc,
    )
    response = interaction_room_routes.get_interaction_room(request, room_id=room.id)
    assert response.status_code == 200
    assert b"get_interaction_room" in response.body
