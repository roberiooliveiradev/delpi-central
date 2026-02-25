# app/application/use_cases/remove_group_roles_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class RemoveRoleFromGroupUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_id: str, role_id: str):
        gid = UUID(group_id)
        rid = UUID(role_id)

        self.uow.group_roles.remove_role(gid, rid)
        self.uow.commit()

        user_ids = self.uow.rbac_queries.list_user_ids_by_group(gid)

        for uid in user_ids:
            self.uow.cache.invalidate(str(uid))

        return {"ok": True}