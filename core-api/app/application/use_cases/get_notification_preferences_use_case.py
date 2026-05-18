# app/application/use_cases/get_notification_preferences_use_case.py

from dataclasses import dataclass

from app.application.unit_of_work import UnitOfWork
from app.domain.notifications.notification_preference_policy import MUTABLE_NOTIFICATION_CATEGORIES


@dataclass
class NotificationPreferencesResult:
    muted_categories: list[str]
    mutable_categories: list[str]


class GetNotificationPreferencesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str) -> NotificationPreferencesResult:
        muted = self.uow.notification_preferences.get_muted_categories(user_id)
        return NotificationPreferencesResult(
            muted_categories=muted,
            mutable_categories=sorted(MUTABLE_NOTIFICATION_CATEGORIES),
        )
