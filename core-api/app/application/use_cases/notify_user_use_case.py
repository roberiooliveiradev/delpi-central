# app/application/use_cases/notify_user_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.domain.events.notification_events import UserNotifiedEvent
from app.domain.ports.notification_repository import NotificationDTO


class NotifyUserUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(
        self,
        user_id: str,
        title: str | None,
        message: str,
        type: str = "info",
    ):

        # 1️⃣ Cria notificação
        notification = NotificationDTO(
            id=None,  # será gerado no repo
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            read=False,
            created_at=None,
        )

        notification_id = self.uow.notifications.create(notification)

        # 2️⃣ Registra evento de domínio
        self.uow.collect_event(
            UserNotifiedEvent(
                notification_id=str(notification_id),
                user_id=user_id,
                title=title,
                message=message,
                type=type,
            )
        )

        return {"id": str(notification_id)}