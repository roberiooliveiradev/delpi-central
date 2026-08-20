from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from starlette.requests import Request

from commercial_app.domain.entities.interaction_room import InteractionMessage
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


def _message() -> InteractionMessage:
    return InteractionMessage(
        id=UUID("00000000-0000-0000-0000-000000000222"),
        room_id=UUID("00000000-0000-0000-0000-000000000111"),
        message_kind="text",
        body_text="olá",
        created_at=datetime.now(timezone.utc),
        author_user_id="user-room-test",
    )


def test_list_messages_403() -> None:
    request = _request("/interaction-rooms/x/messages")
    request.state.user = _User([])
    response = interaction_room_routes.list_interaction_messages(
        request,
        room_id=uuid4(),
    )
    assert response.status_code == 403


def test_post_message_201(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request("/interaction-rooms/x/messages", method="POST")
    request.state.user = _User(["commercial.access"])
    msg = _message()
    fake_uc = MagicMock()
    fake_uc.post.return_value = msg
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_messages_use_case",
        lambda: fake_uc,
    )
    body = SimpleNamespace(
        body_text="olá",
        message_kind="text",
        parent_id=None,
        mentions=None,
    )
    response = interaction_room_routes.post_interaction_message(
        request,
        room_id=msg.room_id,
        body=body,
    )
    assert response.status_code == 201
    assert b"post_interaction_message" in response.body


def test_update_and_delete_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    msg = _message()
    fake_uc = MagicMock()
    fake_uc.update.return_value = msg
    fake_uc.delete.return_value = msg
    monkeypatch.setattr(
        interaction_room_routes,
        "build_manage_interaction_messages_use_case",
        lambda: fake_uc,
    )
    request = _request("/interaction-rooms/x/messages/y", method="PATCH")
    request.state.user = _User(["commercial.access"])
    update_body = SimpleNamespace(body_text="editado", mentions=None)
    updated = interaction_room_routes.update_interaction_message(
        request,
        room_id=msg.room_id,
        message_id=msg.id,
        body=update_body,
    )
    assert updated.status_code == 200
    assert b"update_interaction_message" in updated.body
    fake_uc.update.assert_called_once()
    call_kwargs = fake_uc.update.call_args.kwargs
    assert call_kwargs["body_text"] == "editado"
    assert call_kwargs["replace_mentions"] is False

    update_with_mentions = SimpleNamespace(
        body_text="editado @Ana",
        mentions=[{"mention_kind": "user", "ref": {"user_id": "u2"}, "label": "@Ana"}],
    )
    fake_uc.update.reset_mock()
    updated_mentions = interaction_room_routes.update_interaction_message(
        request,
        room_id=msg.room_id,
        message_id=msg.id,
        body=update_with_mentions,
    )
    assert updated_mentions.status_code == 200
    mention_kwargs = fake_uc.update.call_args.kwargs
    assert mention_kwargs["replace_mentions"] is True
    assert mention_kwargs["mentions"] is not None

    delete_req = _request("/interaction-rooms/x/messages/y", method="DELETE")
    delete_req.state.user = _User(["commercial.access"])
    deleted = interaction_room_routes.delete_interaction_message(
        delete_req,
        room_id=msg.room_id,
        message_id=msg.id,
    )
    assert deleted.status_code == 200
    assert b"delete_interaction_message" in deleted.body
