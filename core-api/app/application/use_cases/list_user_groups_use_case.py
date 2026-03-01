# app/application/use_cases/list_user_groups_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class ListUserGroupsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str):
        uid = UUID(user_id)

        group_ids = self.uow.user_groups.list_group_ids(uid)

        groups = []
        for gid in group_ids:
            group = self.uow.groups.get(gid)
            if group:
                groups.append({
                    "id": str(group.id),
                    "name": group.name,
                    "description": group.description,
                })

        return groups