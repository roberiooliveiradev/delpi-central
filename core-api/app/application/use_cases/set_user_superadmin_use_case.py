# app/application/use_cases/set_user_superadmin_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class SetUserSuperadminUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, is_superadmin: bool):

        uid = UUID(user_id)

        # 1️⃣ Atualiza flag
        self.uow.users.set_superadmin(uid, is_superadmin)

        # 2️⃣ Invalida cache RBAC
        if self.uow.cache:
            self.uow.cache.invalidate(str(uid))

        # 3️⃣ Dispara evento global
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="user_superadmin_updated",
                payload={
                    "userId": user_id,
                    "is_superadmin": is_superadmin,
                },
                target_user_id=None,  # broadcast
            )
        )

        return {"ok": True}