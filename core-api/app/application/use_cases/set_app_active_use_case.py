# app/application/use_cases/set_app_active_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class SetAppActiveUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, app_id: str, active: bool):

        # 1️⃣ Regra de negócio
        self.uow.admin_apps.set_active(app_id, active)

        # 2️⃣ Evento reativo
        self.uow.collect_event(
            AdminChangedEvent(
                entity="apps",
                action="app_activated" if active else "app_deactivated",
                payload={
                    "appId": app_id,
                    "active": active,
                },
                target_user_id=None,  # broadcast
            )
        )

        return {"ok": True}