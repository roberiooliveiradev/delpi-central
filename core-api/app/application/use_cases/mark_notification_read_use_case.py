# app/application/use_cases/mark_notification_read_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class MarkNotificationReadUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, notification_id: str):
        self.uow.notifications.mark_read(UUID(notification_id))
        self.uow.commit()