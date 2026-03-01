# app/application/use_cases/mark_all_notifications_read_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.domain.events.notification_events import (
    AllNotificationsMarkedReadEvent,
)


class MarkAllNotificationsReadUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str):

        # 1️⃣ Regra de negócio
        self.uow.notifications.mark_all_read(user_id)

        # 2️⃣ Registrar evento
        self.uow.collect_event(
            AllNotificationsMarkedReadEvent(
                user_id=user_id
            )
        )

        return {"ok": True}