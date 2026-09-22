"""GET/POST /data/copilot/* — retired (410 Gone → VISTA gpt-actions)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tv_app.main import app


async def _bypass_auth_middleware(request, call_next):
    return await call_next(request)


@pytest.mark.parametrize(
    "method,path,json_body",
    [
        ("get", "/data/copilot/capabilities", None),
        ("post", "/data/copilot/suggest-ops", {"message": "crie um slide"}),
        (
            "post",
            "/data/copilot/preview-patch",
            {"target": {}, "ops": [{"op": "create_playlist", "name": "X"}]},
        ),
        (
            "post",
            "/data/copilot/apply-patch",
            {"target": {}, "ops": [{"op": "create_playlist", "name": "X"}]},
        ),
        ("get", "/data/copilot/telemetry", None),
    ],
)
def test_copilot_http_surface_returns_410_gone(method, path, json_body):
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
        request = getattr(client, method)
        response = request(path, json=json_body) if json_body is not None else request(path)

    assert response.status_code == 410
    body = response.json()
    assert body["success"] is False
    assert body["data"]["gone"] is True
    assert body["data"]["successor"] == "/gpt-actions/v1"
    assert body["data"]["mutationOwner"] == "PresentationMutation"
