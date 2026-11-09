# app/tests/test_me_controller.py

from unittest.mock import patch
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


def test_get_me_endpoint(client, app):
    user_id = str(uuid4())

    @app.before_request
    def inject_user():
        g.current_user = type(
            "User",
            (),
            {
                "id": user_id,
                "name": "Rob",
                "email": "rob@delpi.com",
                "is_superadmin": False,
                "roles": [],
                "groups": [],
                "permissions": ["crm.access"],
            },
        )()
        g.current_permissions = ["crm.access"]

    with patch(
        "app.interfaces.http.me_controller.SqlAlchemyUnitOfWork"
    ) as uow_cls:
        uow = uow_cls.return_value.__enter__.return_value
        uow.consents.list_by_user.return_value = []

        response = client.get("/me")

    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == user_id
    assert data["name"] == "Rob"
    assert data["permissions"] == ["crm.access"]


def test_get_me_apps_endpoint(client, app):
    user_id = str(uuid4())

    @app.before_request
    def inject_user():
        g.current_user = type(
            "User",
            (),
            {
                "id": user_id,
                "permissions": [],
                "is_superadmin": False,
            },
        )()
        g.current_permissions = []

    with patch(
        "app.interfaces.http.me_controller.ListUserAppsUseCase"
    ) as MockUseCase, patch(
        "app.interfaces.http.me_controller.SqlAlchemyUnitOfWork"
    ) as uow_cls:
        from types import SimpleNamespace

        uow_cls.return_value.__enter__.return_value = SimpleNamespace(
            app_queries=object()
        )
        uow_cls.return_value.__exit__.return_value = False
        MockUseCase.return_value.execute.return_value = [
            {"id": "crm", "name": "CRM"}
        ]

        response = client.get("/me/apps")

    assert response.status_code == 200
    assert response.get_json()[0]["id"] == "crm"


def test_get_me_access_profile_endpoint(client, app):
    user_id = str(uuid4())

    @app.before_request
    def inject_user():
        g.current_user = type(
            "User",
            (),
            {"id": user_id, "is_superadmin": False},
        )()
        g.current_permissions = []

    with patch(
        "app.interfaces.http.me_controller.GetMyAccessProfileUseCase"
    ) as MockUseCase, patch(
        "app.interfaces.http.me_controller.SqlAlchemyUnitOfWork"
    ) as uow_cls:
        uow_cls.return_value.__enter__.return_value = object()
        uow_cls.return_value.__exit__.return_value = False
        MockUseCase.return_value.execute.return_value = {
            "roles": [],
            "groups": [],
        }

        response = client.get("/me/access-profile")

    assert response.status_code == 200
    assert "roles" in response.get_json()
