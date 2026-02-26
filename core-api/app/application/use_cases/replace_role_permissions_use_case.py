# app/application/use_cases/replace_role_permissions_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class ReplaceRolePermissionsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_id: str, permission_ids: list[str]):
        rid = UUID(role_id)

        self.uow.role_permissions.replace_permissions_by_ids(
            rid,
            permission_ids
        )
        self.uow.commit()

        user_ids = set(self.uow.rbac_queries.list_user_ids_by_role(rid))
        user_ids |= set(self.uow.rbac_queries.list_user_ids_by_group_role(rid))

        for uid in user_ids:
            self.uow.cache.invalidate(str(uid))

        return {"ok": True}