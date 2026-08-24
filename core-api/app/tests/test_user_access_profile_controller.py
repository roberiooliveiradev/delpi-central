# app/tests/test_user_access_profile_controller.py

from unittest.mock import MagicMock, patch
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


def test_get_user_access_profile_requires_auth(client):
    user_id = uuid4()
    response = client.get(f"/admin/rbac/users/{user_id}/access-profile")
    assert response.status_code == 401


@patch("app.interfaces.http.rbac_controller.GetUserAccessProfileUseCase")
@patch("app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork")
def test_get_user_access_profile_success(mock_uow, mock_uc, client, app):
    user_id = uuid4()
    user = MagicMock(is_superadmin=False)
    mock_uow.return_value.__enter__.return_value.users.get_by_id.return_value = user
    mock_uc.return_value.execute.return_value = {
        "isSuperadmin": False,
        "roles": [],
        "groups": [],
        "effectivePermissions": [],
        "effectiveApps": [],
    }

    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=True)
            response = client.get(
                f"/admin/rbac/users/{user_id}/access-profile",
            )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["roles"] == []
    mock_uc.return_value.execute.assert_called_once()


@patch("app.interfaces.http.rbac_controller.GetUserAccessProfileUseCase")
@patch("app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork")
def test_get_user_access_profile_not_found(mock_uow, mock_uc, client, app):
    user_id = uuid4()
    mock_uow.return_value.__enter__.return_value.users.get_by_id.return_value = None

    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=True)
            response = client.get(
                f"/admin/rbac/users/{user_id}/access-profile",
            )

    assert response.status_code == 404
    mock_uc.return_value.execute.assert_not_called()


@patch("app.interfaces.http.rbac_controller.GetUserAccessProfileUseCase")
@patch("app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork")
def test_get_user_access_profile_forbidden_without_permission(mock_uow, mock_uc, client, app):
    user_id = uuid4()

    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=False, permissions=[])
            response = client.get(
                f"/admin/rbac/users/{user_id}/access-profile",
            )

    assert response.status_code == 403
    mock_uc.return_value.execute.assert_not_called()
