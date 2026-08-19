"""Pins da sala de interação — use case + HTTP."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from starlette.requests import Request

from commercial_app.application.use_cases.manage_interaction_messages import (
    ManageInteractionMessagesUseCase,
    PostInteractionMessageInput,
)
from commercial_app.domain.entities.interaction_room import InteractionPin
from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)
from commercial_app.interface.http.routes import interaction_room_routes
from tests.test_interaction_message_use_case import InMemoryInteractionMessageRepo
from tests.test_interaction_room_membership_use_case import InMemoryInteractionRoomRepo


class _User:
    def __init__(self, permissions: list[str], sub: str = "user-pin"):
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


def _seed_member_and_message() -> tuple[
    InMemoryInteractionRoomRepo,
    InMemoryInteractionMessageRepo,
    UUID,
    UUID,
]:
    rooms = InMemoryInteractionRoomRepo()
    messages = InMemoryInteractionMessageRepo()
    from commercial_app.application.use_cases.manage_interaction_rooms import (
        ManageInteractionRoomsUseCase,
        ResolveInteractionRoomInput,
    )

    room = ManageInteractionRoomsUseCase(repository=rooms).resolve(
        ResolveInteractionRoomInput(
            kind="entity",
            actor_user_id="user-pin",
            entity_type="order",
            entity_key="01|1",
            title="Pedido",
        )
    )
    uc = ManageInteractionMessagesUseCase(rooms=rooms, messages=messages)
    message = uc.post(
        PostInteractionMessageInput(
            room_id=room.id,
            actor_user_id="user-pin",
            body_text="fixar isto",
        )
    )
    return rooms, messages, room.id, message.id


def test_pin_list_and_unpin_use_case() -> None:
    rooms, messages, room_id, message_id = _seed_member_and_message()
    uc = ManageInteractionMessagesUseCase(rooms=rooms, messages=messages)

    pin = uc.pin(
        room_id=room_id,
        message_id=message_id,
        actor_user_id="user-pin",
    )
    assert pin.message_id == message_id
    assert pin.room_id == room_id

    listed = uc.list_pins(room_id=room_id, actor_user_id="user-pin")
    assert len(listed) == 1
    assert listed[0].id == pin.id

    assert uc.unpin(
        room_id=room_id,
        message_id=message_id,
        actor_user_id="user-pin",
    )
    assert uc.list_pins(room_id=room_id, actor_user_id="user-pin") == []


def test_pin_allows_non_member() -> None:
    rooms, messages, room_id, message_id = _seed_member_and_message()
    uc = ManageInteractionMessagesUseCase(rooms=rooms, messages=messages)
    pin = uc.pin(
        room_id=room_id,
        message_id=message_id,
        actor_user_id="stranger",
    )
    assert pin.message_id == message_id


def test_pin_routes_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    room_id = uuid4()
    message_id = uuid4()
    pin = InteractionPin(
        id=uuid4(),
        room_id=room_id,
        message_id=message_id,
        pinned_by_user_id="user-pin",
        created_at=datetime.now(timezone.utc),
    )
    fake_uc = MagicMock()
    fake_uc.list_pins.return_value = [pin]
    fake_uc.pin.return_value = pin
    fake_uc.unpin.return_value = True
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_messages_use_case",
        lambda: fake_uc,
    )

    list_req = _request(f"/interaction-rooms/{room_id}/pins")
    list_req.state.user = _User(["commercial.access"])
    listed = interaction_room_routes.list_interaction_room_pins(
        list_req,
        room_id=room_id,
    )
    assert listed.status_code == 200
    assert b"list_interaction_room_pins" in listed.body

    pin_req = _request(
        f"/interaction-rooms/{room_id}/messages/{message_id}/pin",
        method="POST",
    )
    pin_req.state.user = _User(["commercial.access"])
    pinned = interaction_room_routes.pin_interaction_message(
        pin_req,
        room_id=room_id,
        message_id=message_id,
    )
    assert pinned.status_code == 201
    assert b"pin_interaction_message" in pinned.body

    unpin_req = _request(
        f"/interaction-rooms/{room_id}/messages/{message_id}/pin",
        method="DELETE",
    )
    unpin_req.state.user = _User(["commercial.access"])
    unpinned = interaction_room_routes.unpin_interaction_message(
        unpin_req,
        room_id=room_id,
        message_id=message_id,
    )
    assert unpinned.status_code == 200
    assert b"unpin_interaction_message" in unpinned.body
