"""GLPI #887: admin identity-review is read-only and never links by names."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from flask import g

from app.application.services.organization_identity_review_service import (
    OrganizationIdentityReviewService,
)
from app.create_app import create_app


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def _member(registration, name, *, mapped_user_id=None):
    return {
        "registration": registration,
        "fullName": name,
        "branchCode": "02",
        "active": True,
        "relationship": "direct",
        "managerRegistration": "20001",
        "identityStatus": "mapped" if mapped_user_id else "unmapped",
        "coreUserId": mapped_user_id,
    }


def _user(name, *, active=True, uid=None):
    return SimpleNamespace(id=uid or uuid4(), name=name, active=active)


def _review(members, users, *, occupied=None, details=False):
    team_service = MagicMock()
    team_service.get_team.return_value = {"members": members}
    user_repo = MagicMock()
    user_repo.list_all.return_value = users
    bindings = MagicMock()
    bindings.get_allocated_registrations.return_value = occupied or {}
    review = OrganizationIdentityReviewService(team_service, user_repo, bindings)
    return review.get_review("20001", include_indirect=True, details=details), bindings


def test_one_exact_name_is_unverified_suggestion_and_creates_no_mapping():
    c = _user(" JoAo   da   SILVA ")
    result, bindings = _review(
        [_member("00007", "joao da silva")], [c], details=True
    )
    assert result["suggestionCount"] == 1
    assert result["verifiedCount"] == 0
    assert result["automaticMappingsCreated"] == 0
    assert result["members"][0]["suggestedCoreUserId"] == str(c.id)
    assert result["members"][0]["verified"] is False
    assert "email" not in str(result).lower()
    bindings.get_allocated_registrations.assert_called_once_with({c.id})
    bindings.upsert.assert_not_called()
    bindings.delete.assert_not_called()


def test_no_exact_name_is_not_misrepresented_as_no_account():
    result, _ = _review(
        [_member("00007", "COLABORADOR RH")], [_user("OUTRA CONTA")],
        details=True,
    )
    assert result["statusCounts"]["no_exact_name_suggestion"] == 1
    assert result["members"][0]["suggestedCoreUserId"] is None


def test_duplicate_rh_names_do_not_reuse_single_core_user():
    user = _user("MARIA TESTE")
    result, _ = _review(
        [_member("00007", "MARIA TESTE"), _member("00008", "maria teste")],
        [user], details=True,
    )
    assert result["suggestionCount"] == 0
    assert result["statusCounts"]["ambiguous_rh_name"] == 2


def test_duplicate_core_names_are_ambiguous():
    result, _ = _review(
        [_member("00007", "MARIA TESTE")],
        [_user("MARIA TESTE"), _user("maria teste")],
        details=True,
    )
    assert result["suggestionCount"] == 0
    assert result["statusCounts"]["ambiguous_core_name"] == 1


def test_already_mapped_core_account_cannot_be_suggested_for_new_registration():
    core_user = _user("NOME UM")
    result, _ = _review(
        [_member("00007", "NOME UM")], [core_user],
        occupied={str(core_user.id): "00009"}, details=True,
    )
    assert result["statusCounts"]["already_assigned_to_other_registration"] == 1
    assert result["members"][0]["suggestedCoreUserId"] is None


def test_existing_verified_mapping_does_not_depend_on_name():
    uid = str(uuid4())
    result, _ = _review(
        [_member("00007", "NOME DIVERGENTE", mapped_user_id=uid)],
        [_user("OUTRA COISA")], details=True,
    )
    assert result["verifiedCount"] == 1
    assert result["suggestionCount"] == 0
    assert result["members"][0]["mappedCoreUserId"] == uid


def test_inactive_core_account_not_suggested_and_default_is_aggregate_only():
    result, _ = _review(
        [_member("00007", "NOME UM")], [_user("NOME UM", active=False)]
    )
    assert result["statusCounts"]["no_exact_name_suggestion"] == 1
    assert "members" not in result


def test_prevent_unbounded_admin_review():
    members = [_member(str(i), "ALGUEM " + str(i)) for i in range(501)]
    with pytest.raises(ValueError, match="500"):
        _review(members, [])


def test_admin_review_requires_authentication_and_both_permissions(client, app):
    path = "/admin/organization/managers/20001/identity-review"
    assert client.get(path).status_code == 401

    with app.app_context(), client:
        g.current_user = SimpleNamespace(
            id=str(uuid4()), is_superadmin=False, permissions=["users.manage"]
        )
        assert client.get(path).status_code == 403


@patch("app.interfaces.http.organization_controller.OrganizationIdentityReviewService")
@patch("app.interfaces.http.organization_controller.SqlAlchemyUnitOfWork")
def test_authorized_admin_review_defaults_to_aggregates_only(
    mock_uow, mock_review_service, client, app
):
    mock_review_service.return_value.get_review.return_value = {
        "teamCount": 63,
        "verifiedCount": 0,
        "suggestionCount": 0,
        "readOnly": True,
        "automaticMappingsCreated": 0,
    }
    with app.app_context(), client:
        g.current_user = SimpleNamespace(
            id=str(uuid4()), is_superadmin=False,
            permissions=["rbac.manage", "users.manage"],
        )
        response = client.get("/admin/organization/managers/20001/identity-review")
    assert response.status_code == 200
    assert response.json["teamCount"] == 63
    assert "members" not in response.json
    mock_review_service.return_value.get_review.assert_called_once_with(
        "20001", include_indirect=True, details=False
    )
    mock_uow.return_value.__enter__.return_value.hr_registrations.upsert.assert_not_called()


def test_admin_review_rejects_bad_boolean_without_querying_data(client, app):
    with app.app_context(), client:
        g.current_user = SimpleNamespace(
            id=str(uuid4()), is_superadmin=False,
            permissions=["rbac.manage", "users.manage"],
        )
        result = client.get(
            "/admin/organization/managers/20001/identity-review?details=maybe"
        )
    assert result.status_code == 400
