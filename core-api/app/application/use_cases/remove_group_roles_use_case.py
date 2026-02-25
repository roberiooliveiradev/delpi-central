# app/application/use_cases/remove_group_roles_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.cache_port import PermissionCachePort


class RemoveRoleFromGroupUseCase:

    def __init__(self, uow: UnitOfWork, permission_cache: PermissionCachePort | None = None):
        self.uow = uow
        self.permission_cache = permission_cache

    def execute(self, group_id: str, role_id: str):

        gid = UUID(group_id)
        rid = UUID(role_id)

        self.uow.group_roles.remove_role(gid, rid)
        self.uow.commit()

        if self.permission_cache:
            user_ids = self.uow.rbac_queries.list_user_ids_by_group(gid)
            for uid in user_ids:
                self.permission_cache.invalidate(uid)

        return {"ok": True}