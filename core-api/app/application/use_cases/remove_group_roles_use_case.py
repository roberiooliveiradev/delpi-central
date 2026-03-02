# app/application/use_cases/remove_group_roles_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class RemoveRoleFromGroupUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_id: str, role_id: str):

        gid = UUID(group_id)
        rid = UUID(role_id)

        # 1️⃣ Regra de negócio
        self.uow.group_roles.remove_role(gid, rid)

        # 2️⃣ Evento global de RBAC
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="role_removed_from_group",
                payload={
                    "groupId": group_id,
                    "roleId": role_id,
                },
                target_user_id=None,
            )
        )

        return {"ok": True}