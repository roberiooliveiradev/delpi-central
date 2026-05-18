# app/application/use_cases/delete_notification_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.notification_user_access import get_owned_notification
from app.domain.events.admin_events import AdminChangedEvent


class DeleteNotificationUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, notification_id: UUID, actor_user_id: str) -> dict:
        notification = get_owned_notification(self.uow, notification_id, actor_user_id)

        self.uow.notifications.soft_delete(notification_id)

        self.uow.collect_event(
            AdminChangedEvent(
                entity="notifications",
                action="notification_deleted",
                payload={"notificationId": str(notification_id)},
                target_user_id=str(notification.user_id),
            )
        )

        return {"ok": True}
