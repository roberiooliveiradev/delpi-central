# app/application/use_cases/resolve_notification_recipients_use_case.py

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.services.notification_recipient_resolution import (
    resolve_notification_recipient_users,
)
from app.application.unit_of_work import UnitOfWork


class ResolveNotificationRecipientsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, request: DispatchNotificationsRequest) -> list[dict]:
        return resolve_notification_recipient_users(self.uow, request)
