# app/application/use_cases/add_permission_to_role_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.cache_port import PermissionCachePort


class AddPermissionToRoleUseCase:
    def __init__(self, uow: UnitOfWork, permission_cache: PermissionCachePort | None = None):
        self.uow = uow
        self.permission_cache = permission_cache

    def execute(self, role_id: str, permission_code: str):
        rid = UUID(role_id)

        self.uow.role_permissions.add_permission_by_code(rid, permission_code)
        self.uow.commit()

        if self.permission_cache:
            user_ids = set(self.uow.rbac_queries.list_user_ids_by_role(rid))
            user_ids |= set(self.uow.rbac_queries.list_user_ids_by_group_role(rid))
            for uid in user_ids:
                self.permission_cache.invalidate(uid)

        return {"ok": True}