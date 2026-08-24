# app/tests/test_user_usage_statistics_controller.py

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


def test_get_user_usage_statistics_requires_auth(client):
    user_id = uuid4()
    response = client.get(f"/admin/rbac/users/{user_id}/usage")
    assert response.status_code == 401


@patch("app.interfaces.http.rbac_controller.GetUserUsageStatisticsUseCase")
@patch("app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork")
def test_get_user_usage_statistics_success(mock_uow, mock_uc, client, app):
    user_id = uuid4()
    mock_uc.return_value.execute.return_value = {
        "generatedAt": "2026-08-24T12:00:00Z",
        "periodDays": 30,
        "user": {"id": str(user_id), "name": "Maria", "email": "maria@example.com"},
        "consent": {"granted": True},
        "summary": {"totalOpens": 10},
    }

    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=True)
            response = client.get(
                f"/admin/rbac/users/{user_id}/usage?periodDays=30",
            )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["periodDays"] == 30
    assert payload["summary"]["totalOpens"] == 10
    mock_uc.return_value.execute.assert_called_once()


@patch("app.interfaces.http.rbac_controller.GetUserUsageStatisticsUseCase")
@patch("app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork")
def test_get_user_usage_statistics_invalid_period(mock_uow, mock_uc, client, app):
    user_id = uuid4()

    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=True)
            response = client.get(
                f"/admin/rbac/users/{user_id}/usage?periodDays=14",
            )

    assert response.status_code == 400
    mock_uc.return_value.execute.assert_not_called()


@patch("app.interfaces.http.rbac_controller.GetUserUsageStatisticsUseCase")
@patch("app.interfaces.http.rbac_controller.SqlAlchemyUnitOfWork")
def test_get_user_usage_statistics_not_found(mock_uow, mock_uc, client, app):
    user_id = uuid4()
    mock_uc.return_value.execute.side_effect = LookupError("Usuário não encontrado.")

    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=True)
            response = client.get(
                f"/admin/rbac/users/{user_id}/usage?periodDays=30",
            )

    assert response.status_code == 404
