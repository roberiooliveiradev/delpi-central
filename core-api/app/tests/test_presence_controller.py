# app/tests/test_presence_controller.py

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from flask import g

from app.create_app import create_app
from app.infrastructure.presence.in_memory_user_presence_store import (
    InMemoryUserPresenceStore,
)
from app.infrastructure.presence import presence_store_provider as provider


@pytest.fixture
def app():
    provider.reset_user_presence_store()
    application = create_app("testing")
    application.config["USER_PRESENCE_ENABLED"] = True
    provider._store = InMemoryUserPresenceStore(ttl_seconds=90)
    yield application
    provider.reset_user_presence_store()


@pytest.fixture
def client(app):
    return app.test_client()


def test_list_online_users_requires_superadmin(client, app):
    with app.app_context():
        with client:
            g.current_user = type("User", (), {"is_superadmin": False})()
            response = client.get("/admin/users/presence")

    assert response.status_code == 403


def test_list_online_users_returns_enriched_items(client, app):
    user_id = uuid4()

    with app.app_context():
        provider.get_user_presence_store().register(
            user_id=str(user_id),
            session_id="sid-1",
        )

        user_dto = MagicMock(
            id=user_id,
            name="Ana",
            email="ana@test.com",
            active=True,
        )

        with patch(
            "app.interfaces.http.presence_controller.SqlAlchemyUnitOfWork"
        ) as uow_cls:
            uow = uow_cls.return_value.__enter__.return_value
            uow.users.get_by_ids.return_value = [user_dto]

            with client:
                g.current_user = type("User", (), {"is_superadmin": True})()
                response = client.get("/admin/users/presence")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["total"] == 1
    assert payload["items"][0]["email"] == "ana@test.com"
    assert payload["enabled"] is True
