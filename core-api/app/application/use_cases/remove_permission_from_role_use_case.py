# app/application/use_cases/remove_permission_from_role_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class RemovePermissionFromRoleUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_id: str, permission_code: str):
        rid = UUID(role_id)

        self.uow.role_permissions.remove_permission_by_code(rid, permission_code)
        self.uow.commit()

        user_ids = set(self.uow.rbac_queries.list_user_ids_by_role(rid))
        user_ids |= set(self.uow.rbac_queries.list_user_ids_by_group_role(rid))

        for uid in user_ids:
            self.uow.cache.invalidate(str(uid))

        return {"ok": True}