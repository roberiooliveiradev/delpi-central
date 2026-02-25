# app/application/use_cases/remove_role_from_user_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.cache_port import PermissionCachePort


class RemoveRoleFromUserUseCase:

    def __init__(self, uow: UnitOfWork, permission_cache: PermissionCachePort | None = None):
        self.uow = uow
        self.permission_cache = permission_cache

    def execute(self, user_id: str, role_id: str):

        uid = UUID(user_id)
        rid = UUID(role_id)

        self.uow.user_roles.remove_role(uid, rid)
        self.uow.commit()

        if self.permission_cache:
            self.permission_cache.invalidate(user_id)

        return {"ok": True}