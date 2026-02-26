# app/application/use_cases/bulk_set_plugins_active_use_case.py

from dataclasses import dataclass
from typing import List, Dict, Any
from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class BulkSetPluginsActiveResult:
    success: bool
    updated: int
    errors: List[Dict[str, Any]]


class BulkSetPluginsActiveUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, ids: List[str], active: bool) -> BulkSetPluginsActiveResult:

        if not ids:
            return BulkSetPluginsActiveResult(
                success=False,
                updated=0,
                errors=[{
                    "code": "validation_error",
                    "message": "ids must be a non-empty list",
                    "path": "ids"
                }]
            )

        updated = 0

        try:
            for plugin_id in ids:
                plugin = self._uow.plugins.get_by_id(plugin_id)
                if not plugin:
                    continue

                plugin.active = active
                updated += 1

            self._uow.commit()

            return BulkSetPluginsActiveResult(
                success=True,
                updated=updated,
                errors=[]
            )

        except Exception as e:
            self._uow.rollback()

            return BulkSetPluginsActiveResult(
                success=False,
                updated=0,
                errors=[{
                    "code": "bulk_activation_failed",
                    "message": str(e),
                    "path": "_global"
                }]
            )