# app/application/use_cases/remove_group_from_user_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.cache_port import PermissionCachePort


class RemoveGroupFromUserUseCase:
    def __init__(self, uow: UnitOfWork, permission_cache: PermissionCachePort | None = None):
        self.uow = uow
        self.permission_cache = permission_cache

    def execute(self, user_id: str, group_id: str):
        uid = UUID(user_id)
        gid = UUID(group_id)

        self.uow.user_groups.remove_group(uid, gid)
        self.uow.commit()

        if self.permission_cache:
            self.permission_cache.invalidate(user_id)

        return {"ok": True}