# app/tests/test_admin_statistics_controller.py

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


def test_get_admin_statistics_requires_permission(client, app):
    with app.app_context():
        with client:
            g.current_user = MagicMock(is_superadmin=False)
            g.current_permissions = []

            response = client.get("/admin/statistics")

    assert response.status_code == 403


def test_get_admin_statistics_success(client, app):
    snapshot = {
        "generatedAt": "2026-05-19T12:00:00Z",
        "users": {"total": 10, "online": 2},
        "apps": {"total": 3},
        "roles": {"total": 5},
        "groups": {"total": 2},
        "permissions": {"total": 20},
        "notifications": {"dispatchesTotal": 4},
        "assignments": {},
    }

    with patch(
        "app.interfaces.http.admin_statistics_controller.GetAdminStatisticsUseCase"
    ) as use_case_cls:
        use_case_cls.return_value.execute.return_value = snapshot

        with app.app_context():
            with client:
                g.current_user = MagicMock(is_superadmin=True)
                g.current_permissions = ["rbac.manage"]

                response = client.get("/admin/statistics")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["users"]["total"] == 10
    assert payload["users"]["online"] == 2
