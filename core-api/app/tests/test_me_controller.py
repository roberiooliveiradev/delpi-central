# app/tests/test_me_controller.py

import pytest
from flask import g

from app.create_app import create_app


@pytest.fixture
def app():
    app = create_app("testing")
    return app


@pytest.fixture
def client(app):
    return app.test_client()

def test_get_me_endpoint(client, app):
    with app.app_context():
        with client:
            g.current_user = type(
                "User",
                (),
                {
                    "id": "123",
                    "name": "Rob",
                    "email": "rob@delpi.com",
                    "is_superadmin": False,
                },
            )()
            g.current_permissions = ["crm.access"]

            response = client.get("/me")

            assert response.status_code == 200
            data = response.get_json()

            assert data["id"] == "123"
            assert data["name"] == "Rob"
            assert data["permissions"] == ["crm.access"]

from unittest.mock import patch


def test_get_me_apps_endpoint(client, app):
    with patch(
        "app.interfaces.http.me_controller.ListUserAppsUseCase"
    ) as MockUseCase:
        instance = MockUseCase.return_value
        instance.execute.return_value = [
            {"id": "crm", "name": "CRM"}
        ]

        with app.app_context():
            with client:
                g.current_user = type(
                    "User",
                    (),
                    {"id": "123"}
                )()
                g.current_permissions = []

                response = client.get("/me/apps")

                assert response.status_code == 200
                data = response.get_json()

                assert data[0]["id"] == "crm"


def test_get_me_routes_endpoint(client, app):
    with patch(
        "app.interfaces.http.me_controller.ListUserRoutesUseCase"
    ) as MockUseCase:
        instance = MockUseCase.return_value
        instance.execute.return_value = [
            {"path": "/crm"}
        ]

        with app.app_context():
            with client:
                g.current_user = type(
                    "User",
                    (),
                    {"id": "123"}
                )()
                g.current_permissions = ["crm.access"]

                response = client.get("/me/routes")

                assert response.status_code == 200
                data = response.get_json()

                assert data[0]["path"] == "/crm"