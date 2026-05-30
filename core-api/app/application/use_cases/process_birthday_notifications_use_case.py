# app/application/use_cases/process_birthday_notifications_use_case.py

from dataclasses import dataclass
from datetime import date

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.dispatch_notifications_use_case import (
    DispatchNotificationsUseCase,
)
from app.domain.notifications.notification_automation import build_template_dispatch_request


@dataclass
class ProcessBirthdayNotificationsResult:
    eligible: int
    sent: int
    skipped: int


class ProcessBirthdayNotificationsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, *, on_date: date | None = None) -> ProcessBirthdayNotificationsResult:
        target_date = on_date or date.today()
        user_ids = self.uow.users.list_active_ids_with_birthday_on(
            month=target_date.month,
            day=target_date.day,
        )

        sent = 0
        skipped = 0

        from uuid import UUID

        from app.domain.services.usage_tracking_consent_service import (
            user_has_birthday_notifications_consent,
        )

        for user_id in user_ids:
            if not user_has_birthday_notifications_consent(self.uow, UUID(str(user_id))):
                skipped += 1
                continue

            if self.uow.notifications.has_category_notification_on_date(
                user_id,
                "birthday",
                target_date,
            ):
                skipped += 1
                continue

            request = build_template_dispatch_request(
                template_id="birthday_v1",
                user_ids=[user_id],
                source_app="birthday-automation",
            )
            DispatchNotificationsUseCase(self.uow).execute(request)
            sent += 1

        return ProcessBirthdayNotificationsResult(
            eligible=len(user_ids),
            sent=sent,
            skipped=skipped,
        )
