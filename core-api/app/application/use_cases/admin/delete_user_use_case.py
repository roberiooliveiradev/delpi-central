# app/application/use_cases/delete_user_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class DeleteUserUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str):

        uid = UUID(user_id)

        self.uow.user_roles.delete_by_user_id(uid)
        self.uow.user_groups.delete_by_user_id(uid)

        self.uow.users.delete(uid)

        return {"ok": True}