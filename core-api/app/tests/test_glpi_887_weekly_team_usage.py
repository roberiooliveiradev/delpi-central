"""GLPI #887: week boundary, mapping/consent/privacy and controller access."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from flask import g

from app.application.services.organization_weekly_usage_service import (
    OrganizationWeeklyUsageService,
    week_window,
)
from app.create_app import create_app


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def _member(registration, *, user_id=None):
    return {
        "registration": registration,
        "fullName": "PESSOA " + registration,
        "branchCode": "02",
        "relationship": "direct",
        "identityStatus": "mapped" if user_id else "unmapped",
        "coreUserId": str(user_id) if user_id else None,
    }


def _report(members, consented, events, *, details=False, week_start="2026-11-09"):
    team = MagicMock()
    team.get_team.return_value = {"members": members}
    repo = MagicMock()
    repo.consented_active_user_ids.return_value = set(consented)
    repo.app_opens.return_value = events
    report = OrganizationWeeklyUsageService(team, repo).get_weekly_report(
        "20001",
        week_start=week_start,
        include_indirect=True,
        details=details,
        now_utc=datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc),
    )
    return report, team, repo


def test_default_week_is_previous_completed_local_week():
    monday, since, until = week_window(
        None, now_utc=datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)
    )
    assert monday.isoformat() == "2026-11-09"
    assert since.isoformat() == "2026-11-09T03:00:00"
    assert until.isoformat() == "2026-11-16T03:00:00"
    assert (until - since).days == 7


@pytest.mark.parametrize("wrong", [
    "2026-11-11",  # Wednesday, not Monday
    "2026-11-16",  # Current incomplete week
    "2026-11-23",  # Future
    "2026-01-05",  # More than 90 days ago
    "2026-99-99",  # Invalid date
    "",
])
def test_week_window_rejects_bad_or_incomplete_weeks(wrong):
    with pytest.raises(ValueError):
        week_window(
            wrong, now_utc=datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)
        )


def test_week_window_rejects_naive_clock():
    with pytest.raises(ValueError):
        week_window(None, now_utc=datetime(2026, 11, 18, 0, 0))


def test_report_includes_only_verified_consented_team_members():
    consented = uuid4()
    without_consent = uuid4()
    result, team, repo = _report(
        [
            _member("00001", user_id=consented),
            _member("00002", user_id=without_consent),
            _member("00003"),
        ],
        {consented},
        [
            {"userId": str(consented), "appId": "rhdelpi", "appName": "Portal RH", "count": 3},
            {"userId": str(consented), "appId": "reports", "appName": "Delpi Reports", "count": 2},
        ],
        details=True,
    )
    assert result["teamCount"] == 3
    assert result["verifiedMapped"] == 2
    assert result["unmapped"] == 1
    assert result["consentGranted"] == 1
    assert result["consentNotGranted"] == 1
    assert result["totalRecordedOpens"] == 5
    assert result["withRecordedOpens"] == 1
    assert result["withoutRecordedOpens"] == 0
    assert result["reportSent"] is False
    assert result["readOnly"] is True
    assert result["members"][0]["totalRecordedOpens"] == 5
    assert result["members"][1]["totalRecordedOpens"] is None
    assert result["members"][1]["usageStatus"] == "consent_not_granted"
    assert result["members"][1]["apps"] == []
    assert result["members"][2]["usageStatus"] == "unmapped"
    assert result["members"][2]["totalRecordedOpens"] is None
    team.get_team.assert_called_once_with(
        "20001", include_indirect=True, include_inactive=False
    )
    repo.consented_active_user_ids.assert_called_once_with({consented, without_consent})
    repo.app_opens.assert_called_once()
    assert repo.app_opens.call_args.kwargs["user_ids"] == {consented}
    assert "email" not in str(result).lower()
    assert "routePath" not in str(result)


def test_consent_with_no_events_is_zero_not_missing():
    uid = uuid4()
    report, _, _ = _report([_member("00001", user_id=uid)], {uid}, [], details=True)
    assert report["withRecordedOpens"] == 0
    assert report["withoutRecordedOpens"] == 1
    assert report["members"][0]["usageStatus"] == "no_recorded_opens"
    assert report["members"][0]["totalRecordedOpens"] == 0


def test_default_report_is_aggregated_no_names():
    uid = uuid4()
    report, _, _ = _report(
        [_member("00001", user_id=uid)],
        {uid},
        [{"userId": str(uid), "appId": "reports", "appName": "Reports", "count": 1}],
    )
    assert "members" not in report
    assert report["totalRecordedOpens"] == 1
    assert "PESSOA" not in str(report)


def test_no_consent_means_no_usage_query_and_no_zero_misclassification():
    uid = uuid4()
    team = MagicMock()
    team.get_team.return_value = {"members": [_member("00001", user_id=uid)]}
    repo = MagicMock()
    repo.consented_active_user_ids.return_value = set()
    payload = OrganizationWeeklyUsageService(team, repo).get_weekly_report(
        "20001", now_utc=datetime(2026, 11, 18, 15, tzinfo=timezone.utc),
    )
    assert payload["consentNotGranted"] == 1
    assert payload["withRecordedOpens"] == 0
    assert payload["withoutRecordedOpens"] == 0
    repo.app_opens.assert_not_called()


def test_not_mapped_candidate_cannot_be_enrolled_by_name():
    result, _, repo = _report([_member("00001")], set(), [], details=True)
    assert result["verifiedMapped"] == 0
    assert result["members"][0]["usageStatus"] == "unmapped"
    repo.consented_active_user_ids.assert_called_once_with(set())
    repo.app_opens.assert_not_called()


def test_out_of_team_usage_is_rejected():
    uid = uuid4()
    with pytest.raises(ValueError, match="não autorizado"):
        _report(
            [_member("00001", user_id=uid)],
            {uid},
            [{"userId": str(uuid4()), "appId": "rhdelpi", "appName": "RH", "count": 3}],
        )


def test_duplicate_core_identity_is_rejected():
    uid = uuid4()
    with pytest.raises(ValueError, match="repetido"):
        _report([_member("00001", user_id=uid), _member("00002", user_id=uid)], {uid}, [])


def test_team_size_limit_blocks_large_reports():
    with pytest.raises(ValueError, match="500"):
        _report([_member(str(i)) for i in range(501)], set(), [])


def test_weekly_endpoint_requires_authenticated_admin(client, app):
    path = "/admin/organization/managers/20001/weekly-app-opens"
    assert client.get(path).status_code == 401
    with app.app_context(), client:
        g.current_user = SimpleNamespace(
            id=str(uuid4()), is_superadmin=False, permissions=["users.manage"]
        )
        assert client.get(path).status_code == 403


@patch("app.interfaces.http.organization_controller.OrganizationWeeklyUsageService")
@patch("app.interfaces.http.organization_controller.SqlAlchemyUnitOfWork")
def test_weekly_endpoint_returns_aggregate_by_default(mock_uow, mock_service, client, app):
    mock_service.return_value.get_weekly_report.return_value = {
        "teamCount": 63, "totalRecordedOpens": 5, "reportSent": False, "readOnly": True
    }
    with app.app_context(), client:
        g.current_user = SimpleNamespace(
            id=str(uuid4()), is_superadmin=False,
            permissions=["rbac.manage", "users.manage"],
        )
        response = client.get("/admin/organization/managers/20001/weekly-app-opens")
    assert response.status_code == 200
    assert response.json["totalRecordedOpens"] == 5
    mock_service.return_value.get_weekly_report.assert_called_once_with(
        "20001", week_start=None, include_indirect=True, details=False
    )
    mock_uow.return_value.__enter__.return_value.hr_registrations.upsert.assert_not_called()


def test_weekly_endpoint_rejects_invalid_boolean(client, app):
    with app.app_context(), client:
        g.current_user = SimpleNamespace(
            id=str(uuid4()), is_superadmin=False,
            permissions=["rbac.manage", "users.manage"],
        )
        response = client.get(
            "/admin/organization/managers/20001/weekly-app-opens?details=wrong"
        )
    assert response.status_code == 400


def test_generic_service_token_never_grants_admin_access(client, monkeypatch):
    monkeypatch.setenv("CORE_API_INTEGRATIONS_SERVICE_TOKEN", "integration-token")
    response = client.get(
        "/admin/organization/managers/20001/weekly-app-opens",
        headers={"X-Delpi-Service-Token": "integration-token"},
    )
    assert response.status_code == 401
