# app/application/use_cases/notify_user_use_case.py

from app.domain.ports.notification_repository import NotificationRepository, NotificationData
from app.domain.ports.event_dispatcher_port import EventDispatcherPort
from app.application.unit_of_work import UnitOfWork


class NotifyUserUseCase:

    def __init__(
        self,
        uow: UnitOfWork,
        notification_repo: NotificationRepository,
        event_dispatcher: EventDispatcherPort,
    ):
        self.uow = uow
        self.notification_repo = notification_repo
        self.event_dispatcher = event_dispatcher

    def execute(self, user_id: str, title: str | None, message: str, type: str = "info"):
        notification = NotificationData(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
        )

        notification_id = self.notification_repo.create(notification)

        self.uow.commit()

        # Emite via socket
        self.event_dispatcher.emit(
            "notification",
            {
                "id": str(notification_id),
                "title": title,
                "message": message,
                "type": type,
            },
            room=user_id,
        )