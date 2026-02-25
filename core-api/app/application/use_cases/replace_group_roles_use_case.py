# app/application/use_cases/replace_group_roles_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.cache_port import PermissionCachePort


class ReplaceGroupRolesUseCase:

    def __init__(self, uow: UnitOfWork, permission_cache: PermissionCachePort | None = None):
        self.uow = uow
        self.permission_cache = permission_cache

    def execute(self, group_id: str, role_ids: list[str]):

        gid = UUID(group_id)
        rid_list = [UUID(r) for r in role_ids]

        self.uow.group_roles.replace_roles(gid, rid_list)
        self.uow.commit()

        if self.permission_cache:
            user_ids = self.uow.rbac_queries.list_user_ids_by_group(gid)
            for uid in user_ids:
                self.permission_cache.invalidate(uid)

        return {"ok": True}