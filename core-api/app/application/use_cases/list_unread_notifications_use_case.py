# app/application/use_cases/list_unread_notifications_use_case.py

from typing import List
from app.application.unit_of_work import UnitOfWork


class ListUnreadNotificationsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str):
        return self.uow.notifications.list_unread(user_id)
    