# app/application/use_cases/list_group_roles_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class ListGroupRolesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_id: str):
        gid = UUID(group_id)
        role_ids = self.uow.group_roles.list_role_ids(gid)

        return [str(r) for r in role_ids]