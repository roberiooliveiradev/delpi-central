# app/application/use_cases/replace_user_groups_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.cache_port import PermissionCachePort


class ReplaceUserGroupsUseCase:
    def __init__(self, uow: UnitOfWork, permission_cache: PermissionCachePort | None = None):
        self.uow = uow
        self.permission_cache = permission_cache

    def execute(self, user_id: str, group_ids: list[str]):
        uid = UUID(user_id)
        gids = [UUID(g) for g in group_ids]

        self.uow.user_groups.replace_groups(uid, gids)
        self.uow.commit()

        if self.permission_cache:
            self.permission_cache.invalidate(user_id)

        return {"ok": True}