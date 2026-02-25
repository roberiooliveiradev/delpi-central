# app/application/use_cases/list_user_groups_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class ListUserGroupsUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, user_id: str):
        uid = UUID(user_id)
        group_ids = self.uow.user_groups.list_group_ids(uid)
        return {"userId": user_id, "groupIds": [str(g) for g in group_ids]}