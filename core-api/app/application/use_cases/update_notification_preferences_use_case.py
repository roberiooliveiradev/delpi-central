# app/application/use_cases/update_notification_preferences_use_case.py

from app.application.services.notification_app_access_service import (
    filter_mutable_categories_for_user,
    list_accessible_plugin_ids_for_user,
    merge_muted_categories_preserving_hidden,
)
from app.application.services.notification_catalog_service import NotificationCatalogService
from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.get_notification_preferences_use_case import (
    GetNotificationPreferencesUseCase,
    NotificationPreferencesResult,
)
from app.domain.events.admin_events import AdminChangedEvent


class UpdateNotificationPreferencesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, *, muted_categories: list[str]) -> NotificationPreferencesResult:
        catalog = NotificationCatalogService.get()
        accessible_plugins = list_accessible_plugin_ids_for_user(self.uow, user_id)
        visible_mutable = filter_mutable_categories_for_user(
            accessible_plugins,
            catalog=catalog,
        )
        previous = self.uow.notification_preferences.get_muted_categories(user_id)
        safe_muted = merge_muted_categories_preserving_hidden(
            previous,
            muted_categories,
            visible_mutable=visible_mutable,
            all_mutable=catalog.mutable_categories,
        )
        self.uow.notification_preferences.set_muted_categories(user_id, safe_muted)

        self.uow.collect_event(
            AdminChangedEvent(
                entity="notifications",
                action="preferences_updated",
                payload={"mutedCategories": safe_muted},
                target_user_id=user_id,
            )
        )

        return GetNotificationPreferencesUseCase(self.uow).execute(user_id)
