# app/application/use_cases/list_unread_notifications_use_case.py

from typing import List
from app.application.unit_of_work import UnitOfWork


class ListUnreadNotificationsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str) -> List[dict]:
        rows = self.uow.notifications.list_unread(user_id)

        return [
            {
                "user_id": n.user_id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
            }
            for n in rows
        ]