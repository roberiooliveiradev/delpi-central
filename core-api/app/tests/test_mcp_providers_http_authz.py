"""HTTP AuthZ negatives and registration wiring for MCP providers."""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.create_app import create_app


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def test_blueprints_registered():
    from pathlib import Path

    src = (Path(__file__).resolve().parents[1] / "create_app.py").read_text()
    assert "mcp_providers_bp" in src
    assert "integrations_mcp_providers_bp" in src
    assert "register_blueprint(mcp_providers_bp)" in src
    assert "register_blueprint(integrations_mcp_providers_bp)" in src


def test_admin_list_requires_auth(client):
    response = client.get("/admin/mcp-providers")
    # TESTING skips JWT middleware authenticate(); without g.current_user → 401
    assert response.status_code in {401, 403}


def test_admin_list_forbidden_without_permission(client, app):
    with app.test_request_context("/admin/mcp-providers"):
        from flask import g

        g.current_user = SimpleNamespace(
            id=uuid4(),
            is_superadmin=False,
            permissions=["apps.view"],
        )
        # Invoke view directly after decorating context
        from app.interfaces.http.mcp_providers_controller import list_mcp_providers

        with patch(
            "app.interfaces.http.mcp_providers_controller._use_case"
        ) as mocked:
            mocked.return_value.list_providers.return_value = []
            result = list_mcp_providers()
    # require_permission returns a Flask response tuple/object
    if isinstance(result, tuple):
        assert result[1] == 403
    else:
        assert result.status_code == 403


def test_admin_list_allows_manage_view_permission(client, app):
    with app.test_request_context("/admin/mcp-providers"):
        from flask import g

        g.current_user = SimpleNamespace(
            id=uuid4(),
            is_superadmin=False,
            permissions=["mcp_providers.view"],
        )
        from app.interfaces.http.mcp_providers_controller import list_mcp_providers

        with patch(
            "app.interfaces.http.mcp_providers_controller._use_case"
        ) as mocked:
            mocked.return_value.list_providers.return_value = []
            with patch(
                "app.interfaces.http.mcp_providers_controller.db"
            ) as db:
                db.session.commit = MagicMock()
                result = list_mcp_providers()
    body, status = result if isinstance(result, tuple) else (result.get_json(), result.status_code)
    if hasattr(body, "get_json"):
        payload = body.get_json()
        status = body.status_code
    else:
        payload = body if isinstance(body, dict) else body.get_json()
        status = status if isinstance(result, tuple) else result.status_code
    assert status == 200
    assert payload["items"] == []


def test_eligible_requires_service_token(client):
    with patch.dict(
        os.environ,
        {"CORE_API_INTEGRATIONS_SERVICE_TOKEN": "integrations-secret"},
        clear=False,
    ):
        missing = client.get("/integrations/mcp-providers/eligible")
        assert missing.status_code == 401
        wrong = client.get(
            "/integrations/mcp-providers/eligible",
            headers={"X-Delpi-Service-Token": "wrong"},
        )
        assert wrong.status_code == 403


def test_eligible_ok_with_service_token(client):
    with patch.dict(
        os.environ,
        {"CORE_API_INTEGRATIONS_SERVICE_TOKEN": "integrations-secret"},
        clear=False,
    ):
        with patch(
            "app.interfaces.http.integrations_mcp_providers_controller.ManageMcpProvidersUseCase"
        ) as mocked:
            mocked.return_value.list_eligible.return_value = [
                {"providerRef": "davi", "enabled": True}
            ]
            response = client.get(
                "/integrations/mcp-providers/eligible",
                headers={"X-Delpi-Service-Token": "integrations-secret"},
            )
    assert response.status_code == 200
    assert response.get_json()["items"][0]["providerRef"] == "davi"


def test_permissions_seed_contains_mcp_codes():
    from app.infrastructure.seeds.permissions_seed import BASE_PERMISSIONS

    codes = {p["code"] for p in BASE_PERMISSIONS}
    assert "mcp_providers.view" in codes
    assert "mcp_providers.manage" in codes
