# app/application/use_cases/unregister_plugin_use_case.py

from dataclasses import dataclass
from typing import Dict, List

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


@dataclass(frozen=True)
class UnregisterPluginResult:
    success: bool
    errors: List[Dict[str, str]]


class UnregisterPluginUseCase:
    """
    Remove completamente um plugin:
      - versions
      - routes
      - permissions
      - manifest
      - plugin
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str) -> UnregisterPluginResult:

        # 1️⃣ Verifica existência
        plugin = self._uow.plugins.get_by_id(plugin_id)
        if not plugin:
            return UnregisterPluginResult(
                success=False,
                errors=[{
                    "code": "plugin.not_found",
                    "message": "Plugin not found",
                    "path": "_global"
                }],
            )

        # 2️⃣ Verifica dependências
        dependents: List[str] = []

        for row in self._uow.plugin_manifests.list_all():
            mid = str(row.get("app_id") or "").strip()
            manifest = row.get("manifest") or {}
            deps = manifest.get("dependencies") or []

            if isinstance(deps, list) and plugin_id in deps and mid:
                dependents.append(mid)

        if dependents:
            return UnregisterPluginResult(
                success=False,
                errors=[{
                    "code": "plugin.has_dependents",
                    "message": f"Other plugins depend on this plugin: {', '.join(dependents)}",
                    "path": "_global"
                }],
            )

        # 3️⃣ Regra de negócio (transacional)

        self._uow.plugin_versions.delete_by_app(plugin_id)
        self._uow.plugin_routes.delete_by_app(plugin_id)
        self._uow.plugin_permissions.delete_by_module(plugin_id)
        self._uow.plugin_manifests.delete(plugin_id)
        self._uow.plugins.delete(plugin_id)

        # 4️⃣ Evento global
        self._uow.collect_event(
            AdminChangedEvent(
                entity="plugins",
                action="plugin_unregistered",
                payload={
                    "pluginId": plugin_id,
                },
                target_user_id=None,  # broadcast
            )
        )

        return UnregisterPluginResult(
            success=True,
            errors=[]
        )