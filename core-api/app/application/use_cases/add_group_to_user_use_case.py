# app/application/use_cases/add_group_to_user_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class AddGroupToUserUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, group_id: str):

        uid = UUID(user_id)
        gid = UUID(group_id)

        # Command
        self.uow.user_groups.add_group(uid, gid)

        # Transação
        self.uow.commit()

        # Invalidação de cache (via UoW)
        if self.uow.cache:
            self.uow.cache.invalidate(user_id)

        return {"ok": True}