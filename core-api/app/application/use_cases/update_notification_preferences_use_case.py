# app/application/use_cases/update_notification_preferences_use_case.py

from app.application.services.notification_app_access_service import (
    filter_mutable_categories_for_user,
    list_accessible_plugin_ids_for_user,
    merge_preference_categories_preserving_hidden,
)
from app.application.services.notification_catalog_service import NotificationCatalogService
from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.get_notification_preferences_use_case import (
    GetNotificationPreferencesUseCase,
    NotificationPreferencesResult,
)
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.notifications.notification_preference_policy import (
    reconcile_mute_and_important,
)


class UpdateNotificationPreferencesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        user_id: str,
        *,
        muted_categories: list[str],
        important_categories: list[str] | None = None,
    ) -> NotificationPreferencesResult:
        catalog = NotificationCatalogService.get()
        accessible_plugins = list_accessible_plugin_ids_for_user(self.uow, user_id)
        visible_mutable = filter_mutable_categories_for_user(
            accessible_plugins,
            catalog=catalog,
        )
        previous_muted = self.uow.notification_preferences.get_muted_categories(user_id)
        previous_important = self.uow.notification_preferences.get_important_categories(user_id)

        next_important = (
            previous_important if important_categories is None else important_categories
        )

        safe_muted = merge_preference_categories_preserving_hidden(
            previous_muted,
            muted_categories,
            visible_mutable=visible_mutable,
            all_mutable=catalog.mutable_categories,
        )
        safe_important = merge_preference_categories_preserving_hidden(
            previous_important,
            next_important,
            visible_mutable=visible_mutable,
            all_mutable=catalog.mutable_categories,
        )
        safe_muted, safe_important = reconcile_mute_and_important(safe_muted, safe_important)

        newly_important = set(safe_important) - set(previous_important)
        for category in newly_important:
            self.uow.notifications.mark_unread_important_for_category(
                user_id,
                category,
                is_important=True,
            )

        self.uow.notification_preferences.set_preferences(
            user_id,
            muted_categories=safe_muted,
            important_categories=safe_important,
        )

        self.uow.collect_event(
            AdminChangedEvent(
                entity="notifications",
                action="preferences_updated",
                payload={
                    "mutedCategories": safe_muted,
                    "importantCategories": safe_important,
                },
                target_user_id=user_id,
            )
        )

        return GetNotificationPreferencesUseCase(self.uow).execute(user_id)
