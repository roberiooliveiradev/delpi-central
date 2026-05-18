# app/application/use_cases/mark_notification_read_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class NotificationNotFoundError(ValueError):
    pass


class NotificationAccessDeniedError(ValueError):
    pass


class MarkNotificationReadUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, notification_id: UUID, actor_user_id: str):

        notification = self.uow.notifications.get(notification_id)

        if not notification:
            raise NotificationNotFoundError("Notification not found")

        if str(notification.user_id) != str(actor_user_id):
            raise NotificationAccessDeniedError("Notification does not belong to current user")

        if notification.read:
            return {"ok": True}

        self.uow.notifications.mark_read(notification_id)

        self.uow.collect_event(
            AdminChangedEvent(
                entity="notifications",
                action="notification_marked_read",
                payload={"notificationId": str(notification_id)},
                target_user_id=str(notification.user_id),
            )
        )

        return {"ok": True}
