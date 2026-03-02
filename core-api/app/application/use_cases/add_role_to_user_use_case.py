# app/application/use_cases/add_role_to_user_use_case.py
from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.services.iam_sync_service import IamSyncService


class AddRoleToUserUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, role_id: str):

        uid = UUID(user_id)
        rid = UUID(role_id)

        # Regra de negócio
        self.uow.user_roles.add_role(uid, rid)

        # Evento direcionado
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="role_added_to_user",
                payload={
                    "userId": user_id,
                    "roleId": role_id,
                },
                target_user_id=user_id,
            )
        )

        return {"ok": True}