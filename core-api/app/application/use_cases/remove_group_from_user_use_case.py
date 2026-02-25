# app/application/use_cases/remove_group_from_user_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class RemoveGroupFromUserUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, group_id: str):
        uid = UUID(user_id)
        gid = UUID(group_id)

        self.uow.user_groups.remove_group(uid, gid)
        self.uow.commit()

        self.uow.cache.invalidate(user_id)

        return {"ok": True}