# app/application/use_cases/send_welcome_notification_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.dispatch_notifications_use_case import (
    DispatchNotificationsUseCase,
)
from app.domain.notifications.notification_automation import build_template_dispatch_request


class SendWelcomeNotificationUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str) -> dict:
        request = build_template_dispatch_request(
            template_id="welcome_v1",
            user_ids=[user_id],
            source_app="welcome-automation",
        )
        result = DispatchNotificationsUseCase(self.uow).execute(request)
        return {
            "ok": True,
            "createdCount": result.created_count,
            "notificationIds": result.notification_ids,
        }
