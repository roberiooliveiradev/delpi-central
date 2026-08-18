from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from starlette.requests import Request

from commercial_app.domain.entities.interaction_room import InteractionReaction
from commercial_app.interface.http.routes import interaction_room_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "user-room-test"):
        self.permissions = permissions
        self.sub = sub


def _request(path: str, method: str = "PUT") -> Request:
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


def test_set_reaction_403() -> None:
    request = _request("/interaction-rooms/x/messages/y/reactions/ok")
    request.state.user = _User([])
    response = interaction_room_routes.set_interaction_message_reaction(
        request,
        room_id=uuid4(),
        message_id=uuid4(),
        code="ok",
    )
    assert response.status_code == 403


def test_set_and_clear_reaction_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    reaction = InteractionReaction(
        message_id=UUID("00000000-0000-0000-0000-000000000222"),
        user_id="user-room-test",
        code="ok",
        created_at=datetime.now(timezone.utc),
    )
    fake_uc = MagicMock()
    fake_uc.set_reaction.return_value = reaction
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_messages_use_case",
        lambda: fake_uc,
    )
    request = _request("/interaction-rooms/x/messages/y/reactions/ok")
    request.state.user = _User(["commercial.access"])
    room_id = uuid4()
    set_response = interaction_room_routes.set_interaction_message_reaction(
        request,
        room_id=room_id,
        message_id=reaction.message_id,
        code="ok",
    )
    assert set_response.status_code == 200
    assert b"set_interaction_message_reaction" in set_response.body

    clear_req = _request(
        "/interaction-rooms/x/messages/y/reactions/ok",
        method="DELETE",
    )
    clear_req.state.user = _User(["commercial.access"])
    cleared = interaction_room_routes.clear_interaction_message_reaction(
        clear_req,
        room_id=room_id,
        message_id=reaction.message_id,
        code="ok",
    )
    assert cleared.status_code == 200
    assert b"clear_interaction_message_reaction" in cleared.body
