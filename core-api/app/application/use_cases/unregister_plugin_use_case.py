# app/application/use_cases/unregister_plugin_use_case.py

from dataclasses import dataclass
from typing import Dict, List

from app.application.unit_of_work import UnitOfWork


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

        # Verifica dependências
        try:
            dependents: List[str] = []

            for row in self._uow.plugin_manifests.list_all():
                mid = str(row.get("app_id") or "").strip()
                manifest = row.get("manifest") or {}
                deps = manifest.get("dependencies") or []

                if isinstance(deps, list) and plugin_id in deps and mid:
                    dependents.append(mid)

        except Exception:
            return UnregisterPluginResult(
                success=False,
                errors=[{
                    "code": "plugin.dependencies_check_failed",
                    "message": "Failed to check dependencies",
                    "path": "_global"
                }],
            )

        if dependents:
            return UnregisterPluginResult(
                success=False,
                errors=[{
                    "code": "plugin.has_dependents",
                    "message": f"Other plugins depend on this plugin: {', '.join(dependents)}",
                    "path": "_global"
                }],
            )

        try:
            self._uow.plugin_versions.delete_by_app(plugin_id)
            self._uow.plugin_routes.delete_by_app(plugin_id)
            self._uow.plugin_permissions.delete_by_module(plugin_id)
            self._uow.plugin_manifests.delete(plugin_id)
            self._uow.plugins.delete(plugin_id)

            self._uow.commit()
            return UnregisterPluginResult(success=True, errors=[])

        except Exception as e:
            self._uow.rollback()
            return UnregisterPluginResult(
                success=False,
                errors=[{
                    "code": "plugin.unregister_failed",
                    "message": str(e),
                    "path": "_global"
                }],
            )