# app/application/use_cases/mark_all_notifications_read_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class MarkAllNotificationsReadUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str):

        self.uow.notifications.mark_all_read(user_id)

        self.uow.collect_event(
            AdminChangedEvent(
                entity="notifications",
                action="all_notifications_marked_read",
                payload={},
                target_user_id=user_id,
            )
        )

        return {"ok": True}
