# app/application/use_cases/bulk_unregister_plugins_use_case.py

from dataclasses import dataclass
from typing import List, Dict

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


@dataclass(frozen=True)
class BulkUnregisterPluginsResult:
    success: bool
    deleted: int
    errors: List[Dict[str, str]]


class BulkUnregisterPluginsUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, ids: List[str]) -> BulkUnregisterPluginsResult:

        if not ids:
            return BulkUnregisterPluginsResult(
                success=False,
                deleted=0,
                errors=[{
                    "code": "validation_error",
                    "message": "ids must be a non-empty list",
                    "path": "ids"
                }]
            )

        # 1️⃣ Validação prévia
        for plugin_id in ids:
            plugin = self._uow.plugins.get_by_id(plugin_id)
            if not plugin:
                return BulkUnregisterPluginsResult(
                    success=False,
                    deleted=0,
                    errors=[{
                        "code": "plugin.not_found",
                        "message": f"Plugin {plugin_id} not found",
                        "path": "_global"
                    }]
                )

        deleted = 0

        # 2️⃣ Regra de negócio
        for plugin_id in ids:
            self._uow.plugin_versions.delete_by_app(plugin_id)
            self._uow.plugin_routes.delete_by_app(plugin_id)
            self._uow.plugin_permissions.delete_by_module(plugin_id)
            self._uow.plugin_manifests.delete(plugin_id)
            self._uow.plugins.delete(plugin_id)
            deleted += 1

        # 3️⃣ Evento global de plugin
        self._uow.collect_event(
            AdminChangedEvent(
                entity="plugins",
                action="plugins_unregistered",
                payload={
                    "ids": ids,
                    "deleted": deleted,
                },
                target_user_id=None,  # broadcast
            )
        )

        return BulkUnregisterPluginsResult(
            success=True,
            deleted=deleted,
            errors=[]
        )