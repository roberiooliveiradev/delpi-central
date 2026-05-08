# app/application/use_cases/admin/delete_role_use_case.py

from uuid import UUID

from app.application.unit_of_work import UnitOfWork


class DeleteRoleUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_id: str) -> dict:
        rid = UUID(role_id)

        role = self.uow.roles.get(rid)
        if not role:
            return {"ok": True, "deleted": False}

        self.uow.role_permissions.delete_by_role_id(rid)
        self.uow.user_roles.delete_by_role_id(rid)
        self.uow.group_roles.delete_by_role_id(rid)

        self.uow.roles.delete(rid)

        return {"ok": True, "deleted": True}