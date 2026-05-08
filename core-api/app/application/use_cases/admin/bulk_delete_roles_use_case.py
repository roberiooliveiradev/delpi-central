# app/application/use_cases/admin/bulk_delete_roles_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.admin.delete_role_use_case import DeleteRoleUseCase


class BulkDeleteRolesUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, role_ids: list[str]) -> dict:
        if not isinstance(role_ids, list):
            raise ValueError("Campo 'ids' deve ser uma lista.")

        deleted = 0
        skipped = 0

        delete_role_use_case = DeleteRoleUseCase(self.uow)

        for role_id in role_ids:
            result = delete_role_use_case.execute(role_id)

            if result.get("deleted"):
                deleted += 1
            else:
                skipped += 1

        return {
            "ok": True,
            "deleted": deleted,
            "skipped": skipped,
        }