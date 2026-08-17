# app/application/use_cases/get_notification_preferences_use_case.py

from dataclasses import dataclass

from app.application.services.notification_app_access_service import (
    filter_mutable_categories_for_user,
    list_accessible_plugin_ids_for_user,
)
from app.application.services.notification_catalog_icon_service import (
    NotificationCatalogIconService,
)
from app.application.services.notification_catalog_service import NotificationCatalogService
from app.application.unit_of_work import UnitOfWork
from app.domain.notifications.notification_preference_policy import normalize_muted_categories


@dataclass
class NotificationPreferencesResult:
    muted_categories: list[str]
    mutable_categories: list[str]
    categories: list[dict[str, object]]


class GetNotificationPreferencesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str) -> NotificationPreferencesResult:
        catalog = NotificationCatalogService.get()
        accessible_plugins = list_accessible_plugin_ids_for_user(self.uow, user_id)
        visible_mutable = filter_mutable_categories_for_user(
            accessible_plugins,
            catalog=catalog,
        )

        muted = normalize_muted_categories(
            self.uow.notification_preferences.get_muted_categories(user_id),
            mutable_categories=visible_mutable,
        )

        categories = [
            item
            for item in NotificationCatalogIconService.to_api_categories(self.uow.admin_apps)
            if item.get("id") in visible_mutable
        ]

        return NotificationPreferencesResult(
            muted_categories=muted,
            mutable_categories=sorted(visible_mutable),
            categories=categories,
        )
