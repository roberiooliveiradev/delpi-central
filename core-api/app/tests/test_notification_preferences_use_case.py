# app/tests/test_notification_preferences_use_case.py

from unittest.mock import MagicMock, patch

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.services.notification_app_access_service import (
    filter_mutable_categories_for_user,
    merge_muted_categories_preserving_hidden,
)
from app.application.services.notification_catalog_service import NotificationCatalogService
from app.application.use_cases.dispatch_notifications_use_case import (
    DispatchNotificationsUseCase,
)
from app.application.use_cases.get_notification_preferences_use_case import (
    GetNotificationPreferencesUseCase,
)
from app.application.use_cases.update_notification_preferences_use_case import (
    UpdateNotificationPreferencesUseCase,
)
from app.domain.notifications.notification_preference_policy import (
    normalize_muted_categories,
    reconcile_mute_and_important,
)


def test_normalize_muted_categories_ignores_system_and_invalid():
    mutable = NotificationCatalogService.get().mutable_categories
    assert normalize_muted_categories(
        ["announcement", "system", "invalid", "announcement"],
        mutable_categories=mutable,
    ) == [
        "announcement",
    ]


def test_reconcile_mute_and_important_prefers_important():
    muted, important = reconcile_mute_and_important(
        ["announcement", "welcome"],
        ["welcome", "birthday"],
    )
    assert muted == ["announcement"]
    assert important == ["birthday", "welcome"]


def test_filter_mutable_hides_app_without_access():
    visible = filter_mutable_categories_for_user(frozenset({"commercial"}))
    assert "announcement" in visible
    assert "commercial" in visible
    assert "kaizometro" not in visible
    assert "tv_dashboard" not in visible


def test_merge_muted_preserves_hidden_app_silence():
    all_mutable = NotificationCatalogService.get().mutable_categories
    visible = frozenset({"announcement", "welcome"})
    merged = merge_muted_categories_preserving_hidden(
        ["announcement", "kaizometro"],
        ["welcome"],
        visible_mutable=visible,
        all_mutable=all_mutable,
    )
    assert merged == ["kaizometro", "welcome"]


@patch(
    "app.application.use_cases.update_notification_preferences_use_case.list_accessible_plugin_ids_for_user",
    return_value=frozenset(),
)
def test_update_notification_preferences_persists_muted(_mock_plugins):
    uow = MagicMock()
    uow.notification_preferences.get_muted_categories.return_value = ["birthday"]
    uow.notification_preferences.get_important_categories.return_value = []
    uow.admin_apps.get.return_value = None

    result = UpdateNotificationPreferencesUseCase(uow).execute(
        "user-1",
        muted_categories=["birthday", "welcome"],
        important_categories=[],
    )

    uow.notification_preferences.set_preferences.assert_called_once_with(
        "user-1",
        muted_categories=["birthday", "welcome"],
        important_categories=[],
    )
    assert "birthday" in result.muted_categories


@patch(
    "app.application.use_cases.update_notification_preferences_use_case.list_accessible_plugin_ids_for_user",
    return_value=frozenset({"commercial"}),
)
def test_update_marks_unread_when_category_becomes_important(_mock_plugins):
    uow = MagicMock()
    uow.notification_preferences.get_muted_categories.return_value = []
    uow.notification_preferences.get_important_categories.return_value = []
    uow.admin_apps.get.return_value = None

    UpdateNotificationPreferencesUseCase(uow).execute(
        "user-1",
        muted_categories=[],
        important_categories=["commercial"],
    )

    uow.notifications.mark_unread_important_for_category.assert_called_once_with(
        "user-1",
        "commercial",
        is_important=True,
    )


@patch(
    "app.application.use_cases.get_notification_preferences_use_case.list_accessible_plugin_ids_for_user",
    return_value=frozenset({"commercial"}),
)
def test_get_preferences_only_lists_accessible_app_categories(_mock_plugins):
    uow = MagicMock()
    uow.notification_preferences.get_muted_categories.return_value = [
        "commercial",
        "kaizometro",
    ]
    uow.notification_preferences.get_important_categories.return_value = ["commercial"]
    uow.admin_apps.get.return_value = None

    result = GetNotificationPreferencesUseCase(uow).execute("user-1")

    assert "commercial" in result.mutable_categories
    assert "kaizometro" not in result.mutable_categories
    assert "announcement" in result.mutable_categories
    assert result.muted_categories == []
    assert result.important_categories == ["commercial"]
    assert all(item["id"] in result.mutable_categories for item in result.categories)


def test_dispatch_skips_users_who_muted_category():
    uow = MagicMock()
    uow.users.get_by_id.return_value = MagicMock(
        active=True, id="550e8400-e29b-41d4-a716-446655440000"
    )
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
