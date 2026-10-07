# app/tests/test_admin_notification_category_access.py

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from flask import g

from app.create_app import create_app
from app.application.use_cases.list_notification_category_users_use_case import (
    ListNotificationCategoryUsersUseCase,
)
from app.application.use_cases.update_user_notification_category_preference_use_case import (
    UpdateUserNotificationCategoryPreferenceUseCase,
)
from app.domain.ports.notification_preference_repository import (
    NotificationPreferenceDTO,
)

U1 = uuid4()
U2 = uuid4()


def _user(user_id, *, name="User", email="u@x.com", active=True):
    return MagicMock(id=user_id, name=name, email=email, active=active)


def _uow_with_users(users):
    uow = MagicMock()
    uow.users.list_paginated.side_effect = (
        lambda *, q, page, page_size, sort, direction: (
            users[(page - 1) * page_size : page * page_size],
            len(users),
        )
    )
    return uow


def test_category_users_all_active_users_and_flags():
    uow = _uow_with_users([_user(U1), _user(U2), _user(uuid4(), active=False)])
    uow.notification_preferences.get_preferences_for_users.return_value = {
        str(U1): NotificationPreferenceDTO(
            user_id=str(U1),
            muted_categories=["announcement"],
            important_categories=["announcement"],
            email_categories=[],
        )
    }

    result = ListNotificationCategoryUsersUseCase(uow).execute(
        category="announcement",
        page=1,
        page_size=10,
    )

    assert result["total"] == 2
    u1 = next(i for i in result["items"] if i["id"] == str(U1))
    u2 = next(i for i in result["items"] if i["id"] == str(U2))
    assert u1["enabled"] is False
    assert u1["important"] is True
    assert u1["emailEnabled"] is False
    assert u1["email"] == "u@x.com"
    assert u1["mutable"] is True
    assert u2["enabled"] is True
    assert result["hasMore"] is False


def test_category_users_filters_by_app_access():
    uow = _uow_with_users([_user(U1), _user(U2)])
    uow.notification_preferences.get_preferences_for_users.return_value = {}
    uow.app_queries.list_active_apps_with_routes.return_value = [
        MagicMock(id="commercial", base_path="/apps/commercial")
    ]

    with patch(
        "app.application.use_cases.list_notification_category_users_use_case"
        ".DirectoryUserEligibilityService"
    ) as elig:
        elig.return_value.matches.side_effect = (
            lambda user, *, app_id=None, permission_code=None: user.id == U1
        )
        result = ListNotificationCategoryUsersUseCase(uow).execute(
            category="commercial",
            page=1,
            page_size=10,
        )

    assert result["total"] == 1
    assert result["items"][0]["id"] == str(U1)
    assert result["category"]["appId"] == "commercial"


def test_category_users_empty_when_app_inactive():
    uow = _uow_with_users([_user(U1)])
    uow.app_queries.list_active_apps_with_routes.return_value = []

    result = ListNotificationCategoryUsersUseCase(uow).execute(
        category="commercial",
        page=1,
        page_size=10,
    )

    assert result["total"] == 0
    assert result["items"] == []
    uow.notification_preferences.get_preferences_for_users.assert_called_once_with([])


def test_category_users_unknown_category():
    uow = _uow_with_users([])
    with pytest.raises(ValueError):
        ListNotificationCategoryUsersUseCase(uow).execute(category="nope-cat")


def test_category_users_pagination():
    users = [_user(uuid4()) for _ in range(5)]
    uow = _uow_with_users(users)
    uow.notification_preferences.get_preferences_for_users.return_value = {}

    page1 = ListNotificationCategoryUsersUseCase(uow).execute(
        category="announcement", page=1, page_size=2
    )
    page3 = ListNotificationCategoryUsersUseCase(uow).execute(
        category="announcement", page=3, page_size=2
    )
    assert page1["total"] == 5 and page1["hasMore"] is True
    assert len(page1["items"]) == 2
    assert len(page3["items"]) == 1 and page3["hasMore"] is False


def _update_uow():
    uow = MagicMock()
    uow.users.get_by_id.return_value = _user(U1)
    uow.admin_apps.get.return_value = None
    uow.app_queries.list_active_apps_with_routes.return_value = []
    return uow


def test_admin_disable_clears_important_and_email():
    uow = _update_uow()
    uow.notification_preferences.get_muted_categories.return_value = []
    uow.notification_preferences.get_important_categories.return_value = [
        "announcement"
    ]
    uow.notification_preferences.get_email_categories.return_value = ["announcement"]

    UpdateUserNotificationCategoryPreferenceUseCase(uow).execute(
        str(U1), category="announcement", enabled=False
    )

    uow.notification_preferences.set_preferences.assert_called_once_with(
        str(U1),
        muted_categories=["announcement"],
        important_categories=[],
        email_categories=[],
    )


def test_admin_enable_important_unmutes():
    uow = _update_uow()
    uow.notification_preferences.get_muted_categories.return_value = ["announcement"]
    uow.notification_preferences.get_important_categories.return_value = []
    uow.notification_preferences.get_email_categories.return_value = []

    UpdateUserNotificationCategoryPreferenceUseCase(uow).execute(
        str(U1), category="announcement", important=True
    )

    uow.notification_preferences.set_preferences.assert_called_once_with(
        str(U1),
        muted_categories=[],
        important_categories=["announcement"],
        email_categories=[],
    )


def test_admin_update_rejects_invalid_inputs():
    uow = MagicMock()
    uow.users.get_by_id.return_value = _user(U1)
    with pytest.raises(ValueError):
        UpdateUserNotificationCategoryPreferenceUseCase(uow).execute(
            str(U1), category="unknown-cat", enabled=True
        )
    with pytest.raises(ValueError):
        UpdateUserNotificationCategoryPreferenceUseCase(uow).execute(
            str(U1), category="system", enabled=False
        )
    with pytest.raises(ValueError):
        UpdateUserNotificationCategoryPreferenceUseCase(uow).execute(
            str(U1), category="announcement"
        )
    uow.users.get_by_id.return_value = None
    with pytest.raises(LookupError):
        UpdateUserNotificationCategoryPreferenceUseCase(uow).execute(
            str(U1), category="announcement", enabled=True
        )


@pytest.fixture
def app():
    return create_app("testing")


@pytest.fixture
def client(app):
    return app.test_client()


def test_route_category_users_requires_superadmin(client, app):
    with app.app_context():
        with client:
            g.current_user = type("User", (), {"is_superadmin": False})()
            response = client.get(
                "/admin/notifications/category-users?category=announcement"
            )
    assert response.status_code == 403


def test_route_category_users_requires_auth(client):
    response = client.get("/admin/notifications/category-users?category=announcement")
    assert response.status_code == 401


def test_route_category_users_success(client, app):
    with app.app_context():
        with client:
            g.current_user = type("User", (), {"is_superadmin": True})()
            with patch(
                "app.interfaces.http.notifications_controller.SqlAlchemyUnitOfWork"
            ), patch(
                "app.interfaces.http.notifications_controller.ListNotificationCategoryUsersUseCase"
            ) as mock_uc:
                mock_uc.return_value.execute.return_value = {
                    "category": {"id": "announcement"},
                    "items": [],
                    "page": 1,
                    "pageSize": 50,
                    "total": 0,
                    "hasMore": False,
                }
                response = client.get(
                    "/admin/notifications/category-users?category=announcement&page=2&pageSize=10"
                )
    assert response.status_code == 200
    assert response.get_json()["total"] == 0
    mock_uc.return_value.execute.assert_called_once_with(
        category="announcement", q=None, page=2, page_size=10
    )


def test_route_category_users_bad_pagination(client, app):
    with app.app_context():
        with client:
            g.current_user = type("User", (), {"is_superadmin": True})()
            response = client.get(
                "/admin/notifications/category-users?category=announcement&page=abc"
            )
    assert response.status_code == 400


def test_route_update_user_preference_requires_superadmin(client, app):
    with app.app_context():
        with client:
            g.current_user = type("User", (), {"is_superadmin": False})()
            response = client.patch(
                f"/admin/notifications/user-preferences/{U1}",
                json={"category": "announcement", "enabled": False},
            )
    assert response.status_code == 403


def test_route_update_user_preference_rejects_non_bool(client, app):
    with app.app_context():
        with client:
            g.current_user = type("User", (), {"is_superadmin": True})()
            response = client.patch(
                f"/admin/notifications/user-preferences/{U1}",
                json={"category": "announcement", "enabled": "yes"},
            )
    assert response.status_code == 400


def test_route_update_user_preference_success(client, app):
    with app.app_context():
        with client:
            g.current_user = type("User", (), {"is_superadmin": True})()
            with patch(
                "app.interfaces.http.notifications_controller.SqlAlchemyUnitOfWork"
            ), patch(
                "app.interfaces.http.notifications_controller.UpdateUserNotificationCategoryPreferenceUseCase"
            ) as mock_uc:
                mock_uc.return_value.execute.return_value = MagicMock(
                    muted_categories=["announcement"],
                    important_categories=[],
                    email_categories=[],
                )
                response = client.patch(
                    f"/admin/notifications/user-preferences/{U1}",
                    json={"category": "announcement", "enabled": False},
                )
    assert response.status_code == 200
    assert response.get_json()["mutedCategories"] == ["announcement"]
    mock_uc.return_value.execute.assert_called_once_with(
        str(U1), category="announcement", enabled=False, important=None, email=None
    )
