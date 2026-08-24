# app/tests/test_me_usage_controller.py

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


def test_get_my_usage_requires_auth(client):
    response = client.get("/me/usage")
    assert response.status_code == 401


@patch(
    "app.application.use_cases.admin.get_user_usage_statistics_use_case.GetUserUsageStatisticsUseCase"
)
@patch("app.interfaces.http.me_controller.SqlAlchemyUnitOfWork")
def test_get_my_usage_success(mock_uow, mock_uc, client, app):
    user_id = uuid4()
    mock_uc.return_value.execute.return_value = {
        "generatedAt": "2026-08-24T12:00:00Z",
        "periodDays": 30,
        "user": {"id": str(user_id), "name": "Self", "email": "self@example.com"},
        "consent": {"granted": True},
        "summary": {"totalOpens": 3},
    }

    with app.app_context():
        with client:
            g.current_user = MagicMock(id=user_id)
            response = client.get("/me/usage?periodDays=30")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["summary"]["totalOpens"] == 3
    mock_uc.return_value.execute.assert_called_once_with(
        user_id=user_id,
        period_days=30,
    )


@patch(
    "app.application.use_cases.admin.get_user_usage_statistics_use_case.GetUserUsageStatisticsUseCase"
)
@patch("app.interfaces.http.me_controller.SqlAlchemyUnitOfWork")
def test_get_my_usage_invalid_period(mock_uow, mock_uc, client, app):
    user_id = uuid4()

    with app.app_context():
        with client:
            g.current_user = MagicMock(id=user_id)
            response = client.get("/me/usage?periodDays=14")

    assert response.status_code == 400
    mock_uc.return_value.execute.assert_not_called()
