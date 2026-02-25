# app/application/use_cases/replace_role_permissions_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.cache_port import PermissionCachePort


class ReplaceRolePermissionsUseCase:
    def __init__(self, uow: UnitOfWork, permission_cache: PermissionCachePort | None = None):
        self.uow = uow
        self.permission_cache = permission_cache

    def execute(self, role_id: str, permission_codes: list[str]):
        rid = UUID(role_id)

        # 1) Atualiza vínculo Role↔Permission
        self.uow.role_permissions.replace_permissions_by_codes(rid, permission_codes)

        # 2) Commit
        self.uow.commit()

        # 3) Invalida cache dos usuários afetados
        if self.permission_cache:
            user_ids = set(self.uow.rbac_queries.list_user_ids_by_role(rid))
            user_ids |= set(self.uow.rbac_queries.list_user_ids_by_group_role(rid))
            for uid in user_ids:
                self.permission_cache.invalidate(uid)

        return {"ok": True}