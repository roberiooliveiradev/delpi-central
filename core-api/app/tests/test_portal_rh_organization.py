"""GLPI #887 — Portal RH S2S gateway, team projection and access checks."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from flask import g

from app.application.services.organization_team_service import OrganizationTeamService
from app.create_app import create_app
from app.infrastructure.gateways.portal_rh_organization_gateway import (
    PortalRhManagerNotFound,
    PortalRhOrganizationContractError,
    PortalRhOrganizationGateway,
    PortalRhOrganizationUnauthorized,
)
from app.infrastructure.persistence.sqlalchemy.user_hr_registration_repository import (
    SqlAlchemyUserHrRegistrationRepository,
)


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def _person(registration="00001", *, ident=1):
    return {
        "id": ident,
        "registration": registration,
        "full_name": "TEST USER",
        "branch_code": "02",
        "active": True,
    }


def _member(registration="00002", *, ident=2):
    return {
        **_person(registration, ident=ident),
        "manager_id": 1,
        "manager_registration": "00001",
        "relationship": "direct",
    }


def test_registration_preserves_zeros_and_does_not_accept_int():
    assert PortalRhOrganizationGateway.validate_registration("00001") == "00001"
    assert SqlAlchemyUserHrRegistrationRepository.validate_registration("00001") == "00001"
    with pytest.raises(ValueError):
        PortalRhOrganizationGateway.validate_registration(1)
    with pytest.raises(ValueError):
        SqlAlchemyUserHrRegistrationRepository.validate_registration("00/01")


def test_gateway_paginates_and_preserves_hierarchy():
    requests = []

    def respond(request: httpx.Request):
        requests.append(request)
        assert request.headers["X-Delpi-Service-Token"] == "rh-only"
        assert request.url.params["include_indirect"] == "true"
        page = int(request.url.params["page"])
        return httpx.Response(200, json={
            "manager": _person(),
            "members": [_member("00002", ident=2)] if page == 1
            else [{**_member("00003", ident=3), "relationship": "indirect"}],
            "has_next": page == 1,
        })

    gateway = PortalRhOrganizationGateway(
        base_url="https://rh.example.test",
        service_token="rh-only",
        client=httpx.Client(timeout=5.0, transport=httpx.MockTransport(respond)),
    )
    result = gateway.get_team("00001", include_indirect=True)
    assert [item["registration"] for item in result["members"]] == [
        "00002", "00003"
    ]
    assert [int(x.url.params["page"]) for x in requests] == [1, 2]


def test_gateway_404_and_401_are_typed_and_never_echo_token():
    for status, exception in [
        (404, PortalRhManagerNotFound),
        (401, PortalRhOrganizationUnauthorized),
    ]:
        client = httpx.Client(timeout=5.0, 
            transport=httpx.MockTransport(
                lambda request: httpx.Response(status, json={"error": "upstream"})
            )
        )
        gateway = PortalRhOrganizationGateway(
            base_url="https://rh.example.test",
            service_token="super-secret",
            client=client,
        )
        with pytest.raises(exception) as error:
            gateway.get_team("00001")
        assert "super-secret" not in str(error.value)


def test_gateway_rejects_mismatched_manager_and_duplicate_registration():
    payload = {
        "manager": _person("00009"),
        "members": [],
        "has_next": False,
    }
    client = httpx.Client(timeout=5.0, transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json=payload)
    ))
    gateway = PortalRhOrganizationGateway(
        base_url="https://rh.example.test", service_token="rh", client=client
    )
    with pytest.raises(PortalRhOrganizationContractError):
        gateway.get_team("00001")

    payload["manager"] = _person()
    payload["members"] = [_member(), _member()]
    with pytest.raises(PortalRhOrganizationContractError):
        gateway.get_team("00001")


def test_service_does_not_guess_unmapped_users():
    gateway = MagicMock()
    gateway.get_team.return_value = {
        "manager": _person(),
        "members": [_member(), _member("00003", ident=3)],
        "includeIndirect": True,
        "includeInactive": False,
    }
    mappings = MagicMock()
    mappings.get_core_user_ids.return_value = {"00001": "core-mgr", "00002": "core-2"}
    data = OrganizationTeamService(gateway, mappings).get_team(
        "00001", include_indirect=True
    )
    mappings.get_core_user_ids.assert_called_once_with({"00001", "00002", "00003"})
    assert data["manager"]["coreUserId"] == "core-mgr"
    assert data["members"][0]["coreUserId"] == "core-2"
    assert data["members"][1]["coreUserId"] is None
    assert data["members"][1]["identityStatus"] == "unmapped"
    assert data["unmappedCount"] == 1


def test_team_endpoint_requires_dedicated_secret_not_generic(client, monkeypatch):
    monkeypatch.setenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "shared")
    monkeypatch.setenv("CORE_ORGANIZATION_READ_SERVICE_TOKEN", "private")
    url = "/integrations/organization/managers/00001/team"
    assert client.get(url).status_code == 401
    assert client.get(url, headers={"X-Delpi-Service-Token": "shared"}).status_code == 403


@patch("app.interfaces.http.organization_controller.OrganizationTeamService")
@patch("app.interfaces.http.organization_controller.SqlAlchemyUnitOfWork")
def test_team_endpoint_authorized_and_parses_indirect(
    mock_uow, mock_service, client, monkeypatch
):
    monkeypatch.setenv("CORE_ORGANIZATION_READ_SERVICE_TOKEN", "private")
    mock_service.return_value.get_team.return_value = {
        "manager": {"registration": "00001", "coreUserId": None},
        "members": [], "count": 0, "unmappedCount": 0,
    }
    response = client.get(
        "/integrations/organization/managers/00001/team?include_indirect=true",
        headers={"X-Delpi-Service-Token": "private"},
    )
    assert response.status_code == 200
    assert response.get_json()["count"] == 0
    assert mock_service.return_value.get_team.call_args.kwargs["include_indirect"] is True
    assert client.get(
        "/integrations/organization/managers/00001/team?include_indirect=invalid",
        headers={"X-Delpi-Service-Token": "private"},
    ).status_code == 400


def test_admin_hr_mapping_is_privileged_and_requires_confirmation(client, app):
    uid = uuid4()
    url = f"/admin/organization/users/{uid}/hr-registration"
    assert client.put(url, json={"registration": "00001"}).status_code == 401
    with app.app_context(), client:
        g.current_user = SimpleNamespace(id=str(uuid4()), is_superadmin=False, permissions=[])
        assert client.put(url, json={"registration": "00001"}).status_code == 403

    with app.app_context(), client:
        g.current_user = SimpleNamespace(
            id=str(uuid4()),
            is_superadmin=False,
            permissions=["rbac.manage", "users.manage"],
        )
        assert client.put(url, json={"registration": "00001"}).status_code == 422


@patch("app.interfaces.http.organization_controller.PortalRhOrganizationGateway")
@patch("app.interfaces.http.organization_controller.SqlAlchemyUnitOfWork")
def test_admin_hr_mapping_validates_rh_and_audits(
    mock_uow, mock_gateway, client, app
):
    uid = uuid4()
    actor = uuid4()
    mock_gateway.return_value.get_collaborator.return_value = _person()
    uow = mock_uow.return_value.__enter__.return_value
    uow.users.get_by_id.return_value = SimpleNamespace(id=uid, active=True)
    uow.hr_registrations.get_by_user.return_value = None
    uow.hr_registrations.serialize.return_value = {
        "userId": str(uid), "registration": "00001"
    }
    with app.app_context(), client:
        g.current_user = SimpleNamespace(
            id=str(actor), is_superadmin=False,
            permissions=["rbac.manage", "users.manage"],
        )
        response = client.put(
            f"/admin/organization/users/{uid}/hr-registration",
            json={"registration": "00001", "confirmIdentity": True},
        )
    assert response.status_code == 200
    mock_gateway.return_value.get_collaborator.assert_called_once_with("00001")
    uow.hr_registrations.upsert.assert_called_once_with(
        user_id=uid, registration="00001", verified_by_user_id=actor
    )
    uow.audits.log.assert_called_once()


def test_admin_read_requires_manage(client):
    assert client.get(
        f"/admin/organization/users/{uuid4()}/hr-registration"
    ).status_code == 401


def test_inactive_rh_collaborator_never_exposes_core_uuid():
    gateway = MagicMock()
    inactive_member = _member("00002")
    inactive_member["active"] = False
    gateway.get_team.return_value = {
        "manager": _person(),
        "members": [inactive_member],
        "includeIndirect": False,
        "includeInactive": True,
    }
    mappings = MagicMock()
    mappings.get_core_user_ids.return_value = {
        "00001": "core-manager",
        "00002": "core-inactive",
    }
    result = OrganizationTeamService(gateway, mappings).get_team(
        "00001", include_inactive=True
    )
    assert result["members"][0]["active"] is False
    assert result["members"][0]["coreUserId"] is None
    assert result["members"][0]["identityStatus"] == "unmapped"
