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
