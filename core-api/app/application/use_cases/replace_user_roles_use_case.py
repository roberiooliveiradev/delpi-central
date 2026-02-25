# app/application/use_cases/replace_user_roles_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork
from app.domain.ports.cache_port import PermissionCachePort


class ReplaceUserRolesUseCase:

    def __init__(self, uow: UnitOfWork, permission_cache: PermissionCachePort | None = None):
        self.uow = uow
        self.permission_cache = permission_cache

    def execute(self, user_id: str, role_ids: list[str]):

        uid = UUID(user_id)
        rid_list = [UUID(r) for r in role_ids]

        self.uow.user_roles.replace_roles(uid, rid_list)
        self.uow.commit()

        # invalida cache do usuário
        if self.permission_cache:
            self.permission_cache.invalidate(user_id)

        return {"ok": True}