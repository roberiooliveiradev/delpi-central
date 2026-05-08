# app/application/use_cases/admin/delete_group_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork


class DeleteGroupUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_id: str) -> dict:
        gid = UUID(group_id)

        group = self.uow.groups.get(gid)
        if not group:
            return {"ok": True, "deleted": False}

        self.uow.user_groups.delete_by_group_id(gid)
        self.uow.group_roles.delete_by_group_id(gid)

        self.uow.groups.delete(gid)

        return {"ok": True, "deleted": True}