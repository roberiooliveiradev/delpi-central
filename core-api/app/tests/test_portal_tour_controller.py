# app/tests/test_portal_tour_controller.py

from unittest.mock import patch

import pytest
from flask import g

from app.create_app import create_app


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def _auth_user(**overrides):
    base = {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Ana",
        "email": "ana@delpi.com",
        "is_superadmin": False,
        "permissions": ["rbac.manage"],
    }
    base.update(overrides)
    return type("User", (), base)()


def test_get_my_portal_tour_progress(client, app):
    with patch(
        "app.interfaces.http.portal_tour_controller.GetPortalTourProgressUseCase"
    ) as mock_use_case:
        mock_use_case.return_value.execute.return_value = type(
            "Result",
            (),
            {
                "tour_version": None,
                "status": None,
                "completed_quest_ids": [],
                "started_at": None,
                "last_activity_at": None,
                "completed_at": None,
            },
        )()

        with app.app_context():
            with client:
                g.current_user = _auth_user()
                response = client.get("/me/portal-tour")

        assert response.status_code == 200
        assert response.get_json()["completedQuestIds"] == []


def test_sync_my_portal_tour_progress(client, app):
    with patch(
        "app.interfaces.http.portal_tour_controller.SyncPortalTourProgressUseCase"
    ) as mock_use_case:
        mock_use_case.return_value.execute.return_value = type(
            "Result",
            (),
            {
                "tour_version": "2026-06-portal-v6-explore",
                "status": "exploring",
                "completed_quest_ids": ["open-apps"],
                "started_at": None,
                "last_activity_at": None,
                "completed_at": None,
            },
        )()

        with app.app_context():
            with client:
                g.current_user = _auth_user()
                response = client.patch(
                    "/me/portal-tour",
                    json={
                        "tourVersion": "2026-06-portal-v6-explore",
                        "status": "exploring",
                        "completedQuestId": "open-apps",
                    },
                )

        assert response.status_code == 200
        assert response.get_json()["status"] == "exploring"


def test_list_portal_tour_explorers_requires_permission(client, app):
    with app.app_context():
        with client:
            g.current_user = _auth_user(permissions=[])
            response = client.get("/admin/portal-tour/explorers")

    assert response.status_code == 403
