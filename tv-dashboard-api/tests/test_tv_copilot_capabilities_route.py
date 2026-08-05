"""GET /data/copilot/capabilities — catálogo versionado."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from tv_app.main import app


async def _bypass_auth_middleware(request, call_next):
    return await call_next(request)


def test_copilot_capabilities_requires_tv_write_and_returns_catalog():
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.data_api_routes.resolve_user",
            return_value=user,
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
    ):
        response = client.get("/data/copilot/capabilities")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["catalogVersion"]
    assert isinstance(data["capabilities"], list) and data["capabilities"]
    assert "delete_block" in data["allowedOps"]
    assert any(cap.get("op") == "add_blank_slide" for cap in data["capabilities"])


def test_copilot_capabilities_forbidden_without_user():
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.data_api_routes.resolve_user",
            return_value=None,
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
    ):
        response = client.get("/data/copilot/capabilities")

    assert response.status_code == 403
    assert response.json()["success"] is False


def test_copilot_suggest_ops_returns_direct_plan_for_create_slide():
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.data_api_routes.resolve_user",
            return_value=user,
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
    ):
        response = client.post(
            "/data/copilot/suggest-ops",
            json={
                "message": "crie um slide",
                "hostContext": {"playlistId": "pl-1"},
            },
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ready"
    assert data["confirmationPolicy"] == "direct"
    assert data["ops"][0]["op"] == "add_blank_slide"


def test_copilot_suggest_ops_ready_when_slide_is_open():
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.data_api_routes.resolve_user",
            return_value=user,
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
    ):
        response = client.post(
            "/data/copilot/suggest-ops",
            json={
                "message": "adicione o modelo de dados oee",
                "hostContext": {"playlistId": "pl-1", "slideId": "sl-1"},
            },
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "ready"
    assert data["confirmationPolicy"] == "direct"
    assert data["ops"]


def test_copilot_suggest_ops_clarifies_missing_slide_without_invalid_ops():
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.data_api_routes.resolve_user",
            return_value=user,
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
    ):
        response = client.post(
            "/data/copilot/suggest-ops",
            json={
                "message": "adicione o modelo de dados oee",
                "hostContext": {"playlistId": "pl-1"},
            },
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "clarification"
    assert data["clarificationKey"] == "suggestNeedSlideOrCreate"
    assert data["ops"] == []
