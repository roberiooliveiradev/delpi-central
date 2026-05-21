# app/application/use_cases/bulk_set_plugins_active_use_case.py

from dataclasses import dataclass
from typing import List, Dict, Any

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent
from app.infrastructure.persistence.app_audit import apply_app_audit


@dataclass(frozen=True)
class BulkSetPluginsActiveResult:
    success: bool
    updated: int
    errors: List[Dict[str, Any]]


class BulkSetPluginsActiveUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(
        self,
        ids: List[str],
        active: bool,
        *,
        actor_user_id: str | None = None,
        actor_name: str | None = None,
    ) -> BulkSetPluginsActiveResult:

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
            apply_app_audit(
                plugin,
                user_id=actor_user_id,
                name=actor_name,
            )
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
                actor_user_id=actor_user_id,
            )
        )

        return BulkSetPluginsActiveResult(
            success=True,
            updated=updated,
            errors=[]
        )