# app/application/use_cases/bulk_set_plugins_active_use_case.py

from dataclasses import dataclass
from typing import List, Dict, Any

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


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

        # 1️⃣ Regra de negócio
        for plugin_id in ids:
            plugin = self._uow.plugins.get_by_id(plugin_id)
            if not plugin:
                continue

            plugin.active = active
            updated += 1

        # 2️⃣ Evento global de plugin
        self._uow.collect_event(
            AdminChangedEvent(
                entity="plugins",
                action="plugins_activation_changed",
                payload={
                    "ids": ids,
                    "active": active,
                    "updated": updated,
                },
                target_user_id=None,  # broadcast
            )
        )

        return BulkSetPluginsActiveResult(
            success=True,
            updated=updated,
            errors=[]
        )