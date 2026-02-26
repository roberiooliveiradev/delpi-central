# app/application/use_cases/admin/bulk_delete_admin_apps_use_case.py

from dataclasses import dataclass
from typing import List, Dict, Any

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class BulkDeleteResult:
    success: bool
    deleted: int
    errors: List[Dict[str, Any]]


class BulkDeleteAdminAppsUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, ids: List[str]) -> BulkDeleteResult:
        if not ids:
            return BulkDeleteResult(
                success=False,
                deleted=0,
                errors=[{
                    "code": "validation_error",
                    "message": "ids must be a non-empty list",
                    "path": "ids"
                }]
            )

        deleted_count = 0

        try:
            for app_id in ids:
                if not self._uow.admin_apps.get(app_id):
                    continue  # ignora inexistentes (idempotência)

                self._uow.admin_apps.delete(app_id)
                deleted_count += 1

            self._uow.commit()

            return BulkDeleteResult(
                success=True,
                deleted=deleted_count,
                errors=[]
            )

        except Exception as e:
            self._uow.rollback()
            return BulkDeleteResult(
                success=False,
                deleted=0,
                errors=[{
                    "code": "bulk_delete_failed",
                    "message": str(e),
                    "path": "_global"
                }]
            )