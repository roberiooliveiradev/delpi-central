# app/application/use_cases/send_welcome_notification_use_case.py

from app.application.errors.notification_dispatch_errors import (
    DispatchNotificationsValidationError,
)
from app.application.services.automated_notification_dispatch_service import (
    AutomatedNotificationDispatchService,
)
from app.application.unit_of_work import UnitOfWork
from app.domain.notifications.notification_automation import (
    SOURCE_APP_WELCOME_AUTOMATION,
    build_template_dispatch_request,
)


class SendWelcomeNotificationUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str) -> dict:
        normalized_user_id = str(user_id).strip()
        if not normalized_user_id:
            return {"ok": True, "createdCount": 0, "notificationIds": []}

        accepting = self.uow.notification_preferences.filter_user_ids_accepting_category(
            [normalized_user_id],
            "welcome",
        )
        if not accepting:
            return {"ok": True, "createdCount": 0, "notificationIds": []}

        request = build_template_dispatch_request(
            template_id="welcome_v1",
            user_ids=[normalized_user_id],
            source_app=SOURCE_APP_WELCOME_AUTOMATION,
        )

        try:
            result = AutomatedNotificationDispatchService(self.uow).dispatch(
                request,
                created_by_user_id=None,
            )
        except DispatchNotificationsValidationError:
            return {"ok": True, "createdCount": 0, "notificationIds": []}

        return {
            "ok": True,
            "createdCount": result.created_count,
            "notificationIds": result.notification_ids,
        }
