# app/application/use_cases/admin/bulk_delete_groups_use_case.py

from app.application.unit_of_work import UnitOfWork
from app.application.use_cases.admin.delete_group_use_case import DeleteGroupUseCase


class BulkDeleteGroupsUseCase:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def execute(self, group_ids: list[str]) -> dict:
        if not isinstance(group_ids, list):
            raise ValueError("Campo 'ids' deve ser uma lista.")

        deleted = 0
        skipped = 0

        delete_group_use_case = DeleteGroupUseCase(self.uow)

        for group_id in group_ids:
            result = delete_group_use_case.execute(group_id)

            if result.get("deleted"):
                deleted += 1
            else:
                skipped += 1

        return {
            "ok": True,
            "deleted": deleted,
            "skipped": skipped,
        }