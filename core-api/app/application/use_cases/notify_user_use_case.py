# app/application/use_cases/notify_user_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.domain.ports.notification_repository import NotificationDTO


class NotifyUserUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, title: str | None, message: str, type: str = "info"):

        notification = NotificationDTO(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
        )

        notification_id = self.uow.notifications.create(notification)

        self.uow.commit()

        self.uow.events.emit(
            "notification",
            {
                "id": str(notification_id),
                "title": title,
                "message": message,
                "type": type,
            },
            room=user_id,
        )
