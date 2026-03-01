# app/application/use_cases/update_admin_app_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class UpdateAdminAppUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, app_id: str, name: str, description: str | None, icon: str | None):

        # 1️⃣ Regra de negócio
        self.uow.admin_apps.update_metadata(app_id, name, description, icon)

        # 2️⃣ Evento global
        self.uow.collect_event(
            AdminChangedEvent(
                entity="apps",
                action="app_updated",
                payload={
                    "appId": app_id,
                    "name": name,
                },
                target_user_id=None,  # broadcast
            )
        )

        return {"ok": True}