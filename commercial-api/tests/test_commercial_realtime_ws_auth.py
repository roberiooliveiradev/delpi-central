from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocketException

from commercial_app.interface.http.routes.realtime_routes import resolve_websocket_user


def test_resolve_websocket_user_loads_rbac_permissions(monkeypatch):
    monkeypatch.setattr(
        "commercial_app.interface.http.routes.realtime_routes.validate_token",
        lambda _token: {"sub": "user-1", "email": "a@b.c", "name": "Ana"},
    )
    monkeypatch.setattr(
        "commercial_app.interface.http.routes.realtime_routes.load_user_rbac",
        AsyncMock(
            return_value={
                "id": "user-1",
                "email": "a@b.c",
                "name": "Ana",
                "roles": [],
                "groups": [],
                "permissions": ["commercial.access", "commercial.manage"],
                "is_superadmin": False,
            }
        ),
    )

    user = asyncio.run(resolve_websocket_user("fake-token"))
    assert user.id == "user-1"
    assert "commercial.access" in user.permissions


def test_resolve_websocket_user_accepts_accounts_view_without_worklist(monkeypatch):
    monkeypatch.setattr(
        "commercial_app.interface.http.routes.realtime_routes.validate_token",
        lambda _token: {"sub": "user-1", "email": "a@b.c"},
    )
    monkeypatch.setattr(
        "commercial_app.interface.http.routes.realtime_routes.load_user_rbac",
        AsyncMock(
            return_value={
                "id": "user-1",
                "email": "a@b.c",
                "permissions": ["commercial.access"],
                "roles": [],
                "groups": [],
                "is_superadmin": False,
            }
        ),
    )

    user = asyncio.run(resolve_websocket_user("fake-token"))
    assert user.id == "user-1"
    assert "commercial.access" in user.permissions


def test_resolve_websocket_user_rejects_without_commercial_read_or_worklist(monkeypatch):
    monkeypatch.setattr(
        "commercial_app.interface.http.routes.realtime_routes.validate_token",
        lambda _token: {"sub": "user-1", "email": "a@b.c"},
    )
    monkeypatch.setattr(
        "commercial_app.interface.http.routes.realtime_routes.load_user_rbac",
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
    """Regressão: permissões não estão no access token Keycloak."""
    monkeypatch.setattr(
        "commercial_app.interface.http.routes.realtime_routes.validate_token",
        lambda _token: {
            "sub": "user-1",
            "email": "a@b.c",
            "realm_access": {"roles": ["default-roles-delpi"]},
        },
    )
    monkeypatch.setattr(
        "commercial_app.interface.http.routes.realtime_routes.load_user_rbac",
        AsyncMock(side_effect=RuntimeError("core down")),
    )
    monkeypatch.setattr(
        "commercial_app.interface.http.routes.realtime_routes._rbac_from_claims",
        lambda claims, token, rbac_unavailable=False: {
            "id": claims.get("sub"),
            "email": claims.get("email"),
            "name": "Ana",
            "roles": [],
            "groups": [],
            "permissions": [],
            "is_superadmin": False,
            "rbac_unavailable": True,
        },
    )

    with pytest.raises(WebSocketException):
        asyncio.run(resolve_websocket_user("fake-token"))


def test_realtime_ws_path_is_public_for_jwt_middleware():
    from commercial_app.middleware.auth_middleware import _is_commercial_public_path

    assert _is_commercial_public_path("/commercial/realtime/ws") is True
    assert _is_commercial_public_path("/apps/commercial-api/commercial/realtime/ws") is True
    assert _is_commercial_public_path("/me/worklist") is False
