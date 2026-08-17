# app/tests/test_notification_catalog_icon_service.py

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.application.services.notification_catalog_icon_service import (
    NotificationCatalogIconService,
)
from app.application.services.notification_catalog_service import NotificationCatalogService
from app.application.use_cases.get_notification_preferences_use_case import (
    GetNotificationPreferencesUseCase,
)


def test_to_api_categories_uses_published_app_icon():
    admin_apps = MagicMock()
    admin_apps.get.side_effect = lambda app_id: (
        SimpleNamespace(icon="briefcase-business")
        if app_id == "commercial"
        else SimpleNamespace(icon=None)
    )

    by_id = {
        item["id"]: item
        for item in NotificationCatalogIconService.to_api_categories(admin_apps)
    }

    assert by_id["commercial"]["icon"] == "briefcase-business"
    assert by_id["commercial"]["icon"] != NotificationCatalogService.get().categories[
        "commercial"
    ].icon


def test_resolve_icon_for_category_prefers_published():
    icon = NotificationCatalogIconService.resolve_icon_for_category(
        "commercial",
        published_icons={"commercial": "briefcase-business"},
    )
    assert icon == "briefcase-business"


def test_get_preferences_enriches_icons_from_admin_apps():
    uow = MagicMock()
    uow.notification_preferences.get_muted_categories.return_value = []
    uow.admin_apps.get.side_effect = lambda app_id: (
        SimpleNamespace(icon="briefcase-business")
        if app_id == "commercial"
        else None
    )

    result = GetNotificationPreferencesUseCase(uow).execute("user-1")
    commercial = next(item for item in result.categories if item["id"] == "commercial")
    assert commercial["icon"] == "briefcase-business"
