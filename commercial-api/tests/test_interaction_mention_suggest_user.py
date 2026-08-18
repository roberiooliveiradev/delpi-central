from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from starlette.requests import Request

from commercial_app.application.use_cases.suggest_interaction_mentions import (
    SuggestInteractionMentionsUseCase,
)
from commercial_app.interface.http.routes import interaction_room_routes


class _User:
    def __init__(self, permissions: list[str], sub: str = "user-room-test"):
        self.permissions = permissions
        self.sub = sub


class _Directory:
    def search_directory_users(self, *, query=None, limit=20, browse=False):
        if query == "ana":
            return [{"id": "u2", "name": "Ana", "email": "ana@delpi"}]
        return []


def _request() -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/interaction-rooms/mention-suggest",
        "raw_path": b"/interaction-rooms/mention-suggest",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_suggest_user_from_directory() -> None:
    uc = SuggestInteractionMentionsUseCase(_Directory())
    items = uc.suggest(query="ana", kinds=["user"])
    assert items == [
        {
            "kind": "user",
            "label": "Ana",
            "subtitle": "ana@delpi",
            "ref": {"user_id": "u2"},
        }
    ]


def test_suggest_ignores_unknown_and_disabled_kinds() -> None:
    uc = SuggestInteractionMentionsUseCase(_Directory())
    assert uc.suggest(query="ana", kinds=["spaceship"]) == []
    assert uc.suggest(query="ana", kinds=["raw_material"]) == []


def test_suggest_route_403() -> None:
    request = _request()
    request.state.user = _User([])
    response = interaction_room_routes.suggest_interaction_mentions(request)
    assert response.status_code == 403


def test_suggest_route_200(monkeypatch: pytest.MonkeyPatch) -> None:
    request = _request()
    request.state.user = _User(["commercial.access"])
    fake_uc = MagicMock()
    fake_uc.suggest.return_value = [
        {"kind": "user", "label": "Ana", "subtitle": "", "ref": {"user_id": "u2"}}
    ]
    monkeypatch.setattr(
        interaction_room_routes,
        "build_suggest_interaction_mentions_use_case",
        lambda: fake_uc,
    )
    response = interaction_room_routes.suggest_interaction_mentions(request, q="ana")
    assert response.status_code == 200
    assert b"suggest_interaction_mentions" in response.body
    assert b"Ana" in response.body
