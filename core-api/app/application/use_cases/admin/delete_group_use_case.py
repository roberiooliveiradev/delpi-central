# app/application/use_cases/delete_group_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class DeleteGroupUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_id: str):

        gid = UUID(group_id)

        self.uow.user_groups.delete_by_group_id(gid)
        self.uow.group_roles.delete_by_group_id(gid)

        self.uow.groups.delete(gid)

        return {"ok": True}