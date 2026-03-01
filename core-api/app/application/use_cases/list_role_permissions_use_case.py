# app/application/use_cases/list_role_permissions_use_case.py


from uuid import UUID
from app.application.unit_of_work import UnitOfWork


class ListRolePermissionsUseCase:

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_id: str):
        rid = UUID(role_id)

        permissions = self.uow.permission_queries.list_permissions_by_role_id(rid)

        return [
            {
                "id": str(p.id),
                "code": p.code,
                "name": p.description or p.code,
                "module": p.module,
            }
            for p in permissions
        ]