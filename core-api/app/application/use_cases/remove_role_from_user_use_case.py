# app/application/use_cases/remove_role_from_user_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class RemoveRoleFromUserUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str, role_id: str):
        uid = UUID(user_id)
        rid = UUID(role_id)

        self.uow.user_roles.remove_role(uid, rid)
        self.uow.commit()

        self.uow.cache.invalidate(user_id)

        return {"ok": True}