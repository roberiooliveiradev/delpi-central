# app/application/use_cases/replace_group_roles_use_case.py

# app/application/use_cases/replace_group_roles_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


class ReplaceGroupRolesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_id: str, role_ids: list[str]):

        gid = UUID(group_id)
        rid_list = [UUID(r) for r in role_ids]

        # 1️⃣ Regra de negócio
        self.uow.group_roles.replace_roles(gid, rid_list)

        # 2️⃣ Descobre usuários impactados
        user_ids = self.uow.rbac_queries.list_user_ids_by_group(gid)

        # 3️⃣ Invalida cache dos usuários afetados
        if self.uow.cache:
            for uid in user_ids:
                self.uow.cache.invalidate(str(uid))

        # 4️⃣ Registra evento global de RBAC
        self.uow.collect_event(
            AdminChangedEvent(
                entity="rbac",
                action="group_roles_replaced",
                payload={"groupId": group_id},
                target_user_id=None,  # broadcast
            )
        )

        return {"ok": True}