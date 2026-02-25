# app/application/use_cases/replace_group_roles_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class ReplaceGroupRolesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_id: str, role_ids: list[str]):
        gid = UUID(group_id)
        rid_list = [UUID(r) for r in role_ids]

        self.uow.group_roles.replace_roles(gid, rid_list)
        self.uow.commit()

        user_ids = self.uow.rbac_queries.list_user_ids_by_group(gid)

        for uid in user_ids:
            self.uow.cache.invalidate(str(uid))

        return {"ok": True}