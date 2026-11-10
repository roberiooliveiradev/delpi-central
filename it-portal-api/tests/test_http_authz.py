"""AuthN/AuthZ HTTP pelo middleware real `delpi_auth` (positivos e negativos)."""

import pytest
from fastapi.testclient import TestClient

import delpi_auth.middleware.fastapi_auth as fastapi_auth

from it_portal_app.main import app

from tests.conftest import server_payload

SERVER_ROUTES = [
    ("get", "/servers"),
    ("get", "/dashboard"),
    ("get", "/servers/2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11"),
    ("get", "/servers/2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11/notes"),
    ("get", "/servers/2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11/history"),
    ("get", "/action-plans"),
]


def test_health_is_public_and_carries_no_inventory(repository):
    with TestClient(app) as anonymous:
        response = anonymous.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "service": "it-portal-api"}


@pytest.mark.parametrize("method, path", SERVER_ROUTES + [("get", "/me/capabilities")])
def test_data_routes_require_token(method, path, repository):
    with TestClient(app) as anonymous:
        response = getattr(anonymous, method)(path)
    assert response.status_code == 401


@pytest.mark.parametrize("method, path", SERVER_ROUTES)
def test_valid_jwt_without_permissions_is_forbidden(method, path, client, principal):
    principal.permissions = []
    assert getattr(client, method)(path).status_code == 403


@pytest.mark.parametrize("method, path", SERVER_ROUTES)
def test_specific_permission_without_access_is_forbidden(method, path, client, principal):
    principal.permissions = ["it-portal.servers.view", "it-portal.actions.view"]
    assert getattr(client, method)(path).status_code == 403


def test_rbac_unavailable_fails_closed(client, principal):
    principal.rbac_unavailable = True
    assert client.get("/servers").status_code == 503
    assert client.post("/servers", json=server_payload()).status_code == 503


def test_service_principal_cannot_use_portal(client, monkeypatch):
    monkeypatch.setattr(
        fastapi_auth, "request_has_valid_internal_service_token", lambda _request: True
    )
    assert client.get("/servers").status_code == 403


def test_viewer_reads_but_cannot_write(client, principal, repository):
    created = client.post("/servers", json=server_payload())
    assert created.status_code == 201
    server = created.json()["data"]

    principal.permissions = ["it-portal.access", "it-portal.servers.view"]
    assert client.get("/servers").status_code == 200
    assert client.get(f"/servers/{server['id']}").status_code == 200
    assert client.post("/servers", json=server_payload(hostname="srv-2")).status_code == 403
    assert (
        client.put(
            f"/servers/{server['id']}", json={**server_payload(), "revision": 1}
        ).status_code
        == 403
    )
    assert client.post(f"/servers/{server['id']}/archive", json={"revision": 1}).status_code == 403
    assert client.post(f"/servers/{server['id']}/notes", json={"body": "x"}).status_code == 403
    assert client.get("/action-plans").status_code == 403
    assert (
        client.post(
            f"/servers/{server['id']}/action-plans", json={"title": "x", "priority": "low"}
        ).status_code
        == 403
    )
    assert len(repository.servers) == 1


def test_note_permission_is_independent_from_manage(client, principal):
    server = client.post("/servers", json=server_payload()).json()["data"]
    principal.permissions = [
        "it-portal.access",
        "it-portal.servers.view",
        "it-portal.notes.create",
    ]
    response = client.post(f"/servers/{server['id']}/notes", json={"body": "Reiniciado às 22h."})
    assert response.status_code == 201
    assert response.json()["data"]["author_name"] == "Ana TI"


def test_action_viewer_cannot_change_status(client, principal):
    server = client.post("/servers", json=server_payload()).json()["data"]
    plan = client.post(
        f"/servers/{server['id']}/action-plans", json={"title": "Patch", "priority": "high"}
    ).json()["data"]
    principal.permissions = [
        "it-portal.access",
        "it-portal.servers.view",
        "it-portal.actions.view",
    ]
    assert client.get(f"/action-plans/{plan['id']}").status_code == 200
    assert (
        client.post(
            f"/action-plans/{plan['id']}/status", json={"status": "done", "revision": 1}
        ).status_code
        == 403
    )


def test_dashboard_omits_actions_without_actions_view(client, principal):
    principal.permissions = ["it-portal.access", "it-portal.servers.view"]
    data = client.get("/dashboard").json()["data"]
    assert data["action_plans"] is None
    assert data["attention_action_plans"] is None


def test_capabilities_reflect_effective_permissions(client, principal):
    principal.permissions = ["it-portal.access", "it-portal.servers.view", "it-portal.notes.create"]
    data = client.get("/me/capabilities").json()["data"]
    assert data == {
        "display_name": "Ana TI",
        "can_view_servers": True,
        "can_manage_servers": False,
        "can_create_notes": True,
        "can_view_action_plans": False,
        "can_manage_action_plans": False,
    }
    principal.permissions = []
    assert client.get("/me/capabilities").status_code == 403
