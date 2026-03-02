# app/application/use_cases/replace_user_roles_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.services.iam_sync_service import IamSyncService


class ReplaceUserRolesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, role_ids: list[str]):

        uid = UUID(user_id)
        rid_list = [UUID(r) for r in role_ids]

        # 1️⃣ Regra de negócio
        self.uow.user_roles.replace_roles(uid, rid_list)

        # 2️⃣ Invalida cache
        if self.uow.cache:
            self.uow.cache.invalidate(user_id)

        # 3️⃣ Registra evento
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="roles_replaced",
                payload={"userId": user_id},
                target_user_id=user_id,
            )
        )

        return {"ok": True}