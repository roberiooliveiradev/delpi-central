# app/tests/test_engagement_statistics_controller.py

from unittest.mock import MagicMock, patch

import pytest
from flask import g

from app.create_app import create_app


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def test_get_engagement_statistics_requires_auth(client):
    response = client.get("/admin/statistics/engagement")
    assert response.status_code == 401


@patch("app.interfaces.http.admin_statistics_controller.GetEngagementStatisticsUseCase")
@patch("app.interfaces.http.admin_statistics_controller.SqlAlchemyUnitOfWork")
def test_get_engagement_statistics_success(mock_uow, mock_uc, client, app):
    mock_uc.return_value.execute.return_value = {
        "generatedAt": "2026-08-24T12:00:00Z",
        "periodDays": 30,
        "activity": {"dau": 5, "wau": 12, "mau": 40, "stickiness": 12.5},
    }

    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=True)
            response = client.get("/admin/statistics/engagement?periodDays=30")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["periodDays"] == 30
    assert payload["activity"]["dau"] == 5
    mock_uc.return_value.execute.assert_called_once_with(period_days=30)


@patch("app.interfaces.http.admin_statistics_controller.GetEngagementStatisticsUseCase")
@patch("app.interfaces.http.admin_statistics_controller.SqlAlchemyUnitOfWork")
def test_get_engagement_statistics_invalid_period(mock_uow, mock_uc, client, app):
    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=True)
            response = client.get("/admin/statistics/engagement?periodDays=14")

    assert response.status_code == 400
    mock_uc.return_value.execute.assert_not_called()
