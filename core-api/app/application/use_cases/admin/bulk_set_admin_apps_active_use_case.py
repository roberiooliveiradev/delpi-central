# app/application/use_cases/admin/bulk_set_admin_apps_active_use_case.py

from dataclasses import dataclass
from typing import List, Dict, Any

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class BulkSetActiveResult:
    success: bool
    updated: int
    errors: List[Dict[str, Any]]


class BulkSetAdminAppsActiveUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, ids: List[str], active: bool) -> BulkSetActiveResult:
        if not ids:
            return BulkSetActiveResult(
                success=False,
                updated=0,
                errors=[{
                    "code": "validation_error",
                    "message": "ids must be a non-empty list",
                    "path": "ids"
                }]
            )

        updated_count = 0

        try:
            for app_id in ids:
                if not self._uow.admin_apps.get(app_id):
                    continue

                self._uow.admin_apps.set_active(app_id, active)
                updated_count += 1

            self._uow.commit()

            return BulkSetActiveResult(
                success=True,
                updated=updated_count,
                errors=[]
            )

        except Exception as e:
            self._uow.rollback()
            return BulkSetActiveResult(
                success=False,
                updated=0,
                errors=[{
                    "code": "bulk_update_failed",
                    "message": str(e),
                    "path": "_global"
                }]
            )