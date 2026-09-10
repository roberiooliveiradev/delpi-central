from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocketException

from requests_app.interface.http.routes.realtime_routes import resolve_websocket_user


def test_resolve_websocket_user_loads_rbac_permissions(monkeypatch):
    monkeypatch.setattr(
        "requests_app.interface.http.routes.realtime_routes.validate_token",
        lambda _token: {"sub": "user-1", "email": "a@b.c", "name": "Ana"},
    )
    monkeypatch.setattr(
        "requests_app.interface.http.routes.realtime_routes.load_user_rbac",
        AsyncMock(
            return_value={
                "id": "user-1",
                "email": "a@b.c",
                "name": "Ana",
                "roles": [],
                "groups": [],
                "permissions": ["my-requests.access"],
                "is_superadmin": False,
            }
        ),
    )

    user = asyncio.run(resolve_websocket_user("fake-token"))
    assert user.id == "user-1"
    assert "my-requests.access" in user.permissions


def test_resolve_websocket_user_rejects_without_access(monkeypatch):
    monkeypatch.setattr(
        "requests_app.interface.http.routes.realtime_routes.validate_token",
        lambda _token: {"sub": "user-1", "email": "a@b.c"},
    )
    monkeypatch.setattr(
        "requests_app.interface.http.routes.realtime_routes.load_user_rbac",
        AsyncMock(
            return_value={
                "id": "user-1",
                "email": "a@b.c",
                "permissions": ["unrelated.permission"],
                "roles": [],
                "groups": [],
                "is_superadmin": False,
            }
        ),
    )

    with pytest.raises(WebSocketException):
        asyncio.run(resolve_websocket_user("fake-token"))


def test_resolve_websocket_user_rejects_jwt_claims_only_without_rbac(monkeypatch):
    monkeypatch.setattr(
        "requests_app.interface.http.routes.realtime_routes.validate_token",
        lambda _token: {
            "sub": "user-1",
            "email": "a@b.c",
            "realm_access": {"roles": ["default-roles-delpi"]},
        },
    )
    monkeypatch.setattr(
        "requests_app.interface.http.routes.realtime_routes.load_user_rbac",
        AsyncMock(side_effect=RuntimeError("core down")),
    )
    monkeypatch.setattr(
        "requests_app.interface.http.routes.realtime_routes._rbac_from_claims",
        lambda claims, token, rbac_unavailable=False: {
            "id": claims.get("sub"),
            "email": claims.get("email"),
            "permissions": [],
            "roles": [],
            "groups": [],
            "is_superadmin": False,
            "rbac_unavailable": True,
        },
    )

    with pytest.raises(WebSocketException):
        asyncio.run(resolve_websocket_user("fake-token"))
