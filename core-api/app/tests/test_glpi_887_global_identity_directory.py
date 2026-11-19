"""GLPI #887: global identity linking is independent of the RH manager tree."""

from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from flask import g

from app.create_app import create_app


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def _admin():
    return SimpleNamespace(
        id=str(uuid4()),
        is_superadmin=False,
        permissions=["rbac.manage", "users.manage"],
    )


def test_identity_directory_requires_both_admin_permissions(app, client):
    route = "/admin/organization/identity-directory"
    assert client.get(route).status_code == 401
    with app.app_context(), client:
        g.current_user = SimpleNamespace(
            id=str(uuid4()), is_superadmin=False, permissions=["users.manage"]
        )
        assert client.get(route).status_code == 403


@patch("app.interfaces.http.organization_controller.SqlAlchemyUnitOfWork")
def test_directory_returns_all_core_accounts_including_ceo_without_manager_tree(
    mock_uow, app, client,
):
    ceo_id, other_id = uuid4(), uuid4()
    uow = mock_uow.return_value.__enter__.return_value
    uow.users.list_all.return_value = [
        SimpleNamespace(
            id=ceo_id, name="DENNIS GIORGIO PICCOLI",
            email="ceo@example.org", active=True,
        ),
        SimpleNamespace(
            id=other_id, name="FABIANO SCHMITZ",
            email="fabiano@example.org", active=True,
        ),
    ]
    uow.hr_registrations.get_allocated_registrations.return_value = {
        str(other_id): "20001"
    }
    with app.app_context(), client:
        g.current_user = _admin()
        response = client.get("/admin/organization/identity-directory")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["scope"] == "all_core_accounts"
    assert payload["readOnly"] is True
    assert payload["total"] == 2
    assert payload["linked"] == 1
    people = {row["userId"]: row for row in payload["items"]}
    assert people[str(ceo_id)]["registration"] is None
    assert people[str(other_id)]["registration"] == "20001"
    uow.users.list_all.assert_called_once_with()
    uow.hr_registrations.get_allocated_registrations.assert_called_once()
    uow.hr_registrations.upsert.assert_not_called()


def test_rh_identity_preview_requires_admin_permissions(app, client):
    endpoint = "/admin/organization/collaborators/10257/identity-preview"
    assert client.get(endpoint).status_code == 401
    with app.app_context(), client:
        g.current_user = SimpleNamespace(
            id=str(uuid4()), is_superadmin=False, permissions=[]
        )
        assert client.get(endpoint).status_code == 403


@patch("app.interfaces.http.organization_controller.PortalRhOrganizationGateway")
def test_rh_identity_preview_resolves_ceo_by_registration_without_supervisor(
    gateway, app, client,
):
    gateway.return_value.get_collaborator.return_value = {
        "id": 12,
        "registration": "10257",
        "full_name": "DENNIS GIORGIO PICCOLI",
        "branch_code": "01",
        "active": True,
    }
    with app.app_context(), client:
        g.current_user = _admin()
        response = client.get(
            "/admin/organization/collaborators/10257/identity-preview"
        )
    assert response.status_code == 200
    assert response.get_json() == {
        "registration": "10257",
        "fullName": "DENNIS GIORGIO PICCOLI",
        "branchCode": "01",
        "active": True,
        "readOnly": True,
    }
    gateway.return_value.get_collaborator.assert_called_once_with("10257")
    gateway.return_value.get_team.assert_not_called()


@patch("app.interfaces.http.organization_controller.PortalRhOrganizationGateway")
def test_rh_identity_preview_does_not_hide_inactive_identity(gateway, app, client):
    gateway.return_value.get_collaborator.return_value = {
        "id": 13,
        "registration": "10257",
        "full_name": "COLABORADOR INATIVO",
        "branch_code": "01",
        "active": False,
    }
    with app.app_context(), client:
        g.current_user = _admin()
        response = client.get(
            "/admin/organization/collaborators/10257/identity-preview"
        )
    assert response.status_code == 200
    assert response.get_json()["active"] is False


def test_identity_directory_never_changes_confirmation_contract(app, client):
    with app.app_context(), client:
        g.current_user = _admin()
        assert client.put(
            f"/admin/organization/users/{uuid4()}/hr-registration",
            json={"registration": "10257"}
        ).status_code == 422
