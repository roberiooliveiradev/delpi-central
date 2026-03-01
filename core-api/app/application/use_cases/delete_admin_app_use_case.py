# app/application/use_cases/delete_admin_app_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class DeleteAdminAppUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, app_id: str):

        # 1️⃣ Regra de negócio
        self.uow.admin_apps.delete(app_id)

        # 2️⃣ Evento administrativo (broadcast global)
        self.uow.collect_event(
            AdminChangedEvent(
                entity="apps",
                action="app_deleted",
                payload={"appId": app_id},
                target_user_id=None,  # broadcast
            )
        )

        return {"ok": True}