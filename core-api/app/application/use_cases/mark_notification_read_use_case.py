# app/application/use_cases/mark_notification_read_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.events.notification_events import NotificationMarkedReadEvent


class MarkNotificationReadUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, notification_id: UUID):

        # 1️⃣ Descobrir user_id da notificação (precisa existir no repo)
        notification = self.uow.notifications.get(notification_id)

        if not notification:
            raise ValueError("Notification not found")

        # 2️⃣ Marcar como lida
        self.uow.notifications.mark_read(notification_id)

        # 3️⃣ Registrar evento de domínio
        self.uow.collect_event(
            NotificationMarkedReadEvent(
                notification_id=str(notification_id),
                user_id=notification.user_id,
            )
        )

        return {"ok": True}