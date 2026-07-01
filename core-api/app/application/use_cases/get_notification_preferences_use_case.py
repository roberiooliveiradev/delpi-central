# app/application/use_cases/get_notification_preferences_use_case.py

from dataclasses import dataclass

from app.application.services.notification_catalog_service import NotificationCatalogService
from app.application.unit_of_work import UnitOfWork


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
        muted = self.uow.notification_preferences.get_muted_categories(user_id)
        return NotificationPreferencesResult(
            muted_categories=muted,
            mutable_categories=sorted(catalog.mutable_categories),
            categories=catalog.to_api_categories(),
        )
