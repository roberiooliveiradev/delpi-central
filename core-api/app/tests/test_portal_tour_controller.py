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
    ) as mock_progress, patch(
        "app.interfaces.http.portal_tour_controller.GetPortalTourInsightsUseCase"
    ) as mock_insights:
        mock_progress.return_value.execute.return_value = type(
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
        mock_insights.return_value.execute.return_value = type(
            "Insights",
            (),
            {
                "exploration_duration_seconds": None,
                "quests_completed_after_return": 0,
                "return_streak_message": None,
            },
        )()

        with app.app_context():
            with client:
                g.current_user = _auth_user()
                response = client.get("/me/portal-tour")

        assert response.status_code == 200
        body = response.get_json()
        assert body["completedQuestIds"] == []
        assert body["insights"]["returnStreakMessage"] is None


def test_list_portal_tour_top_explorers(client, app):
    with patch(
        "app.interfaces.http.portal_tour_controller.ListPortalTourTopExplorersUseCase"
    ) as mock_use_case:
        mock_use_case.return_value.execute.return_value = type(
            "Result",
            (),
            {
                "period_days": 7,
                "tour_version": "2026-06-portal-v6-explore",
                "items": [
                    type(
                        "Item",
                        (),
                        {
                            "user_id": "22222222-2222-2222-2222-222222222222",
                            "name": "Bruno",
                            "email": "bruno@delpi.com",
                            "tour_version": "2026-06-portal-v6-explore",
                            "quests_in_period": 5,
                            "last_activity_at": None,
                        },
                    )()
                ],
            },
        )()

        with app.app_context():
            with client:
                g.current_user = _auth_user()
                response = client.get("/admin/portal-tour/top-explorers")

        assert response.status_code == 200
        body = response.get_json()
        assert body["periodDays"] == 7
        assert body["items"][0]["questsInPeriod"] == 5


def test_get_my_portal_tour_catalog(client, app):
    with patch(
        "app.interfaces.http.portal_tour_controller.GetPortalTourCatalogUseCase"
    ) as mock_use_case:
        mock_use_case.return_value.execute.return_value = type(
            "Result",
            (),
            {
                "tour_version": "2026-06-portal-v6-explore",
                "quests": [
                    type(
                        "Quest",
                        (),
                        {
                            "id": "open-apps",
                            "title": "Catálogo",
                            "hint": "Abra apps",
                            "category": "apps",
                            "category_label": "Apps",
                            "scope": "sidebar",
                            "optional": False,
                            "introduced_in_version": "2026-06-portal-v6-explore",
                            "is_new": True,
                        },
                    )()
                ],
                "required_quest_ids": ["open-apps"],
                "optional_quest_ids": [],
                "new_quest_ids": ["open-apps"],
                "progress_percent": 0,
                "explorer_level": "Explorador",
                "earned_xp": 0,
                "category_labels": {"apps": "Apps"},
                "category_order": ["apps"],
            },
        )()

        with app.app_context():
            with client:
                g.current_user = _auth_user(permissions=[])
                response = client.get("/me/portal-tour/catalog")

        assert response.status_code == 200
        body = response.get_json()
        assert body["requiredQuestIds"] == ["open-apps"]
        assert body["quests"][0]["isNew"] is True


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
