from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from starlette.requests import Request

from commercial_app.interface.http.routes import attachment_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "u1"):
        self.permissions = permissions
        self.sub = sub


def _request(path: str = "/attachments", method: str = "GET") -> Request:
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


def test_list_room_message_attachments_403_for_non_member(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request()
    request.state.user = _User(["commercial.access"])
    fake_uc = MagicMock()
    fake_uc.list.side_effect = PermissionError("Você não tem acesso a esta sala.")
    monkeypatch.setattr(
        attachment_routes,
        "build_manage_attachments_use_case",
        lambda: fake_uc,
    )
    response = attachment_routes.list_attachments(
        request,
        owner_type="room_message",
        owner_id=str(uuid4()),
    )
    assert response.status_code == 403
    fake_uc.list.assert_called_once()


def test_delete_room_message_does_not_notify_worklist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request = _request(method="DELETE")
    request.state.user = _User(["commercial.access"])
    attachment_id = uuid4()
    fake_uc = MagicMock()
    fake_uc.delete.return_value = {"deleted": True, "id": str(attachment_id)}
    worklist = MagicMock()
    monkeypatch.setattr(
        attachment_routes,
        "build_manage_attachments_use_case",
        lambda: fake_uc,
    )
    monkeypatch.setattr(
        attachment_routes,
        "build_attachment_repository",
        lambda: SimpleNamespace(
            get_by_id=lambda _id: SimpleNamespace(
                owner_type="room_message",
                owner_id=str(uuid4()),
            )
        ),
    )
    monkeypatch.setattr(attachment_routes, "notify_worklist_changed", worklist)
    response = attachment_routes.delete_attachment(request, attachment_id=attachment_id)
    assert response.status_code == 200
    worklist.assert_not_called()
    fake_uc.delete.assert_called_once()
