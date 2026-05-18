# app/application/use_cases/set_notification_important_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.notification_user_access import get_owned_notification
from app.domain.events.admin_events import AdminChangedEvent


class SetNotificationImportantUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        notification_id: UUID,
        actor_user_id: str,
        *,
        is_important: bool,
    ) -> dict:
        notification = get_owned_notification(self.uow, notification_id, actor_user_id)

        self.uow.notifications.set_important(notification_id, is_important=is_important)

        self.uow.collect_event(
            AdminChangedEvent(
                entity="notifications",
                action="notification_important_updated",
                payload={
                    "notificationId": str(notification_id),
                    "isImportant": is_important,
                },
                target_user_id=str(notification.user_id),
            )
        )

        return {"ok": True, "isImportant": is_important}
