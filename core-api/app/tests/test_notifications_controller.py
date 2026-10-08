# app/tests/test_notifications_controller.py

import os
from unittest.mock import MagicMock, patch

import pytest
from flask import g

from app.application.dto.notification_dispatch_response import (
    NotificationDispatchResponse,
)
from app.create_app import create_app


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def test_admin_dispatch_requires_superadmin(client, app):
    with app.app_context():
        with client:
            g.current_user = type("User", (), {"is_superadmin": False})()
            response = client.post("/admin/notifications", json={"message": "x"})

    assert response.status_code == 403


def test_integrations_dispatch_requires_service_token(client):
    with patch.dict(os.environ, {"CORE_API_INTEGRATIONS_SERVICE_TOKEN": "secret-token"}):
        response = client.post(
            "/integrations/notifications",
            json={"message": "hello", "userIds": ["1"]},
        )

    assert response.status_code == 401


def test_integrations_dispatch_with_valid_token(client):
    with patch.dict(os.environ, {"CORE_API_INTEGRATIONS_SERVICE_TOKEN": "secret-token"}):
        with patch(
            "app.interfaces.http.notifications_controller.build_template_registry"
        ) as mock_registry, patch(
            "app.interfaces.http.notifications_controller.SqlAlchemyUnitOfWork"
        ) as mock_uow, patch(
            "app.interfaces.http.notifications_controller.CreateNotificationDispatchUseCase"
        ) as mock_use_case:
            mock_registry.return_value = MagicMock()
            mock_uow.return_value.__enter__.return_value = MagicMock()
            mock_use_case.return_value.execute.return_value = (
                NotificationDispatchResponse(
                    dispatch_id="disp-1",
                    status="completed",
                    scheduled_at=None,
                    created_count=1,
                    notification_ids=["nid"],
                    recipient_count=1,
                )
            )

            response = client.post(
                "/integrations/notifications",
                headers={"X-Delpi-Service-Token": "secret-token"},
                json={"message": "hello", "userIds": ["550e8400-e29b-41d4-a716-446655440000"]},
            )

    assert response.status_code == 201
    data = response.get_json()
    assert data["createdCount"] == 1
