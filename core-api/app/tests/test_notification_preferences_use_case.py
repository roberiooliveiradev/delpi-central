# app/tests/test_notification_preferences_use_case.py

from unittest.mock import MagicMock

from app.application.services.notification_catalog_service import NotificationCatalogService
from app.application.use_cases.dispatch_notifications_use_case import (
    DispatchNotificationsUseCase,
)
from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.use_cases.update_notification_preferences_use_case import (
    UpdateNotificationPreferencesUseCase,
)
from app.domain.notifications.notification_preference_policy import normalize_muted_categories


def test_normalize_muted_categories_ignores_system_and_invalid():
    mutable = NotificationCatalogService.get().mutable_categories
    assert normalize_muted_categories(
        ["announcement", "system", "invalid", "announcement"],
        mutable_categories=mutable,
    ) == [
        "announcement",
    ]


def test_update_notification_preferences_persists_muted():
    uow = MagicMock()
    uow.notification_preferences.get_muted_categories.return_value = ["birthday"]

    result = UpdateNotificationPreferencesUseCase(uow).execute(
        "user-1",
        muted_categories=["birthday", "welcome"],
    )

    uow.notification_preferences.set_muted_categories.assert_called_once_with(
        "user-1",
        ["birthday", "welcome"],
    )
    assert "birthday" in result.muted_categories


def test_dispatch_skips_users_who_muted_category():
    uow = MagicMock()
    uow.users.get_by_id.return_value = MagicMock(active=True, id="550e8400-e29b-41d4-a716-446655440000")
    uow.notification_preferences.filter_user_ids_accepting_category.return_value = []

    request = DispatchNotificationsRequest(
        title=None,
        message="hello",
        type="info",
        category="announcement",
        presentation="text",
        html_content=None,
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata=None,
        expires_at=None,
        broadcast=False,
        user_ids=["550e8400-e29b-41d4-a716-446655440000"],
        emails=[],
        role_ids=[],
        group_ids=[],
    )

    try:
        DispatchNotificationsUseCase(uow).execute(request)
        raised = False
    except Exception as exc:
        raised = True
        assert "no recipients accept" in str(exc).lower()

    assert raised
    uow.notifications.create.assert_not_called()
