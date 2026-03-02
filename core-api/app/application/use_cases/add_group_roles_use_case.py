# core-api/app/application/use_cases/add_group_roles_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class AddRoleToGroupUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_id: str, role_id: str):

        gid = UUID(group_id)
        rid = UUID(role_id)

        # 1️⃣ Regra de negócio pura
        self.uow.group_roles.add_role(gid, rid)

        # 2️⃣ Apenas publica evento
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="role_added_to_group",
                payload={
                    "groupId": group_id,
                    "roleId": role_id,
                },
                target_user_id=None,
            )
        )

        return {"ok": True}