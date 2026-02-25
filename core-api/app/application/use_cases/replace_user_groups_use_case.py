# app/application/use_cases/replace_user_groups_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class ReplaceUserGroupsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, group_ids: list[str]):
        uid = UUID(user_id)
        gids = [UUID(g) for g in group_ids]

        self.uow.user_groups.replace_groups(uid, gids)
        self.uow.commit()

        self.uow.cache.invalidate(user_id)

        return {"ok": True}