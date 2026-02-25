# app/application/use_cases/list_role_permissions_use_case.py

from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class ListRolePermissionsUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_id: str):
        rid = UUID(role_id)
        codes = self.uow.role_permissions.list_permission_codes(rid)
        return {"roleId": role_id, "permissions": sorted(codes)}