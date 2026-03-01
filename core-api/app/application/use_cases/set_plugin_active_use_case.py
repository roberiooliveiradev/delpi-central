# app/application/use_cases/set_plugin_active_use_case.py

from dataclasses import dataclass
from typing import Dict, List

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


@dataclass(frozen=True)
class SetPluginActiveResult:
    success: bool
    errors: List[Dict[str, str]]


class SetPluginActiveUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str, active: bool) -> SetPluginActiveResult:

        plugin = self._uow.plugins.get_by_id(plugin_id)
        if not plugin:
            return SetPluginActiveResult(
                success=False,
                errors=[{
                    "code": "plugin.not_found",
                    "message": "Plugin not found",
                    "path": "_global"
                }]
            )

        # 1️⃣ Regra de negócio
        plugin.active = active

        # 2️⃣ Evento global
        self._uow.collect_event(
            AdminChangedEvent(
                entity="plugins",
                action="plugin_activated" if active else "plugin_deactivated",
                payload={
                    "pluginId": plugin_id,
                    "active": active,
                },
                target_user_id=None,  # broadcast
            )
        )

        return SetPluginActiveResult(success=True, errors=[])