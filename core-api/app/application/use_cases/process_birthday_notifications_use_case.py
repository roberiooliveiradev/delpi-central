# app/application/use_cases/process_birthday_notifications_use_case.py

from dataclasses import dataclass
from datetime import date

from app.application.unit_of_work import UnitOfWork
from app.application.services.automated_notification_dispatch_service import (
    AutomatedNotificationDispatchService,
)
from app.domain.notifications.notification_automation import (
    SOURCE_APP_BIRTHDAY_AUTOMATION,
    build_template_dispatch_request,
)


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

        skipped = 0
        recipient_ids: list[str] = []

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

            accepting = self.uow.notification_preferences.filter_user_ids_accepting_category(
                [str(user_id)],
                "birthday",
            )
            if not accepting:
                skipped += 1
                continue

            recipient_ids.append(str(user_id))

        sent = 0
        if recipient_ids:
            request = build_template_dispatch_request(
                template_id="birthday_v1",
                user_ids=recipient_ids,
                source_app=SOURCE_APP_BIRTHDAY_AUTOMATION,
            )
            result = AutomatedNotificationDispatchService(self.uow).dispatch(
                request,
                created_by_user_id=None,
            )
            sent = result.created_count

        return ProcessBirthdayNotificationsResult(
            eligible=len(user_ids),
            sent=sent,
            skipped=skipped,
        )
