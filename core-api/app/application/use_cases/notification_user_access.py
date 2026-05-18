# app/application/use_cases/notification_user_access.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.ports.notification_repository import NotificationDTO


class NotificationNotFoundError(ValueError):
    pass


class NotificationAccessDeniedError(ValueError):
    pass


def get_owned_notification(
    uow: UnitOfWork,
    notification_id: UUID,
    actor_user_id: str,
) -> NotificationDTO:
    notification = uow.notifications.get(notification_id)

    if not notification:
        raise NotificationNotFoundError("Notification not found")

    if str(notification.user_id) != str(actor_user_id):
        raise NotificationAccessDeniedError("Notification does not belong to current user")

    return notification
