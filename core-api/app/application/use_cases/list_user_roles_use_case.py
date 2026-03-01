# app/application/use_cases/list_user_roles_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork

class ListUserRolesUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str):
        uid = UUID(user_id)

        role_ids = self.uow.user_roles.list_role_ids(uid)

        roles = []
        for rid in role_ids:
            role = self.uow.roles.get(rid)
            if role:
                roles.append({
                    "id": str(role.id),
                    "name": role.name,
                    "description": role.description,
                })

        return roles