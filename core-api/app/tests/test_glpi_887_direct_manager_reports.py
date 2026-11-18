"""GLPI #887: Core S2S report cannot expand beyond direct employees."""

from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.create_app import create_app


@pytest.fixture
def client():
    return create_app("testing").test_client()


@pytest.fixture
def token(monkeypatch):
    monkeypatch.setenv("CORE_REPORTS_DIRECT_USAGE_SERVICE_TOKEN", "reports-only-token")
    monkeypatch.setenv("CORE_ORGANIZATION_READ_SERVICE_TOKEN", "org-read-token")
    monkeypatch.setenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "generic-token")
    return {"X-Delpi-Service-Token": "reports-only-token"}


def _weekly(direct=True):
    return {
        "source": "app_usage_events",
        "managerRegistration": "20001",
        "includeIndirect": False,
        "weekStart": "2026-11-09",
        "weekEndExclusive": "2026-11-16",
        "timezone": "America/Sao_Paulo",
        "teamCount": 1,
        "verifiedMapped": 1,
        "consentGranted": 1,
        "members": [{
            "registration": "00001",
            "fullName": "EMPREGADO TESTE",
            "branchCode": "02",
            "relationship": "direct" if direct else "indirect",
            "usageStatus": "recorded_opens",
            "totalRecordedOpens": 3,
            "apps": [{"appId": "rh", "appName": "Portal RH", "recordedOpens": 3}],
        }],
    }


def test_only_named_reports_token_can_access(client, token):
    path = "/integrations/organization/managers/20001/reports/direct-weekly-opens"
    assert client.get(path).status_code == 401
    for wrong in ("generic-token", "org-read-token", "wrong"):
        assert client.get(
            path, headers={"X-Delpi-Service-Token": wrong}
        ).status_code == 403
    assert client.get(
        path + "?include_indirect=true", headers=token
    ).status_code == 400


@patch("app.interfaces.http.organization_controller.OrganizationWeeklyUsageService")
@patch("app.interfaces.http.organization_controller.OrganizationTeamService")
@patch("app.interfaces.http.organization_controller.SqlAlchemyUnitOfWork")
def test_direct_weekly_enforces_hierarchy_and_verified_manager(
    mock_uow, mock_team, mock_weekly, client, token
):
    user_id = uuid4()
    mock_weekly.return_value.get_weekly_report.return_value = _weekly()
    mock_team.return_value.get_team.return_value = {
        "manager": {
            "registration": "20001", "fullName": "GESTOR TESTE",
            "active": True, "identityStatus": "mapped",
            "coreUserId": str(user_id),
        }
    }
    uow = mock_uow.return_value.__enter__.return_value
    uow.users.get_by_id.return_value = SimpleNamespace(
        id=user_id, active=True, email="gestor@delpi.com.br",
    )
    path = "/integrations/organization/managers/20001/reports/direct-weekly-opens"
    response = client.get(path, headers=token)
    assert response.status_code == 200
    data = response.get_json()
    assert data["directOnly"] is True
    assert data["includeIndirect"] is False
    assert data["recipient"] == {
        "userId": str(user_id), "email": "gestor@delpi.com.br",
    }
    assert len(data["members"]) == 1
    assert data["members"][0]["relationship"] == "direct"
    mock_weekly.return_value.get_weekly_report.assert_called_once_with(
        "20001", week_start=None, include_indirect=False, details=True,
    )
    mock_team.return_value.get_team.assert_called_once_with(
        "20001", include_indirect=False, include_inactive=False,
    )


@patch("app.interfaces.http.organization_controller.OrganizationWeeklyUsageService")
@patch("app.interfaces.http.organization_controller.OrganizationTeamService")
@patch("app.interfaces.http.organization_controller.SqlAlchemyUnitOfWork")
def test_direct_weekly_rejects_indirect_record_even_if_upstream_broken(
    mock_uow, mock_team, mock_weekly, client, token
):
    mock_weekly.return_value.get_weekly_report.return_value = _weekly(direct=False)
    response = client.get(
        "/integrations/organization/managers/20001/reports/direct-weekly-opens",
        headers=token,
    )
    assert response.status_code == 422
    mock_team.return_value.get_team.assert_not_called()


@patch("app.interfaces.http.organization_controller.OrganizationWeeklyUsageService")
@patch("app.interfaces.http.organization_controller.OrganizationTeamService")
@patch("app.interfaces.http.organization_controller.SqlAlchemyUnitOfWork")
def test_direct_weekly_missing_manager_mapping_never_returns_data(
    mock_uow, mock_team, mock_weekly, client, token
):
    mock_weekly.return_value.get_weekly_report.return_value = _weekly()
    mock_team.return_value.get_team.return_value = {
        "manager": {
            "registration": "20001", "fullName": "GESTOR TESTE",
            "active": True, "identityStatus": "unmapped", "coreUserId": None,
        }
    }
    response = client.get(
        "/integrations/organization/managers/20001/reports/direct-weekly-opens",
        headers=token,
    )
    assert response.status_code == 422
    assert "members" not in response.get_json()
