# app/application/use_cases/update_notification_preferences_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.get_notification_preferences_use_case import (
    GetNotificationPreferencesUseCase,
    NotificationPreferencesResult,
)
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.notifications.notification_preference_policy import normalize_muted_categories


class UpdateNotificationPreferencesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, *, muted_categories: list[str]) -> NotificationPreferencesResult:
        safe_muted = normalize_muted_categories(muted_categories)
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
