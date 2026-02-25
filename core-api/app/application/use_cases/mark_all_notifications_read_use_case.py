# app/application/use_cases/mark_all_notifications_read_use_case.py

from app.application.unit_of_work import UnitOfWork


class MarkAllNotificationsReadUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str):
        self.uow.notifications.mark_all_read(user_id)
        self.uow.commit()