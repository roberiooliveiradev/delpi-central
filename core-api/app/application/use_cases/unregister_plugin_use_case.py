# app/application/use_cases/unregister_plugin_use_case.py

from dataclasses import dataclass
from typing import Any, Dict, List

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class UnregisterPluginResult:
    success: bool
    errors: List[Dict[str, Any]]


class UnregisterPluginUseCase:
    """
    Remove completamente um plugin:
      - versions
      - routes
      - permissions (module=plugin_id)
      - manifest
      - app
    Proteção: impede remover se outro manifesto declara dependencies contendo esse plugin_id.
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str) -> UnregisterPluginResult:
        app = self._uow.plugin_repo.get_by_id(plugin_id)
        if not app:
            return UnregisterPluginResult(
                success=False,
                errors=[{"code": "plugin.not_found", "message": "Plugin not found", "path": "_global"}],
            )

        # dependências
        dependents: List[str] = []
        try:
            for row in self._uow.manifest_repo.list_all():
                # row esperado: {"app_id": "...", "manifest": {...}} (ou similar)
                mid = str(row.get("app_id") or "").strip()
                m = row.get("manifest") or {}
                deps = m.get("dependencies") or []
                if isinstance(deps, list) and plugin_id in deps:
                    if mid:
                        dependents.append(mid)
        except Exception:
            # se list_all falhar, melhor bloquear para não causar remoção acidental
            return UnregisterPluginResult(
                success=False,
                errors=[{"code": "plugin.dependencies_check_failed", "message": "Failed to check dependencies", "path": "_global"}],
            )

        if dependents:
            return UnregisterPluginResult(
                success=False,
                errors=[{
                    "code": "plugin.has_dependents",
                    "message": f"Other plugins depend on this plugin: {', '.join(dependents)}",
                    "path": "_global",
                }],
            )

        try:
            self._uow.version_repo.delete_by_app(plugin_id)
            self._uow.route_repo.delete_by_app(plugin_id)
            self._uow.permission_repo.delete_by_module(plugin_id)
            self._uow.manifest_repo.delete(plugin_id)
            self._uow.plugin_repo.delete(plugin_id)

            self._uow.commit()
            return UnregisterPluginResult(success=True, errors=[])

        except Exception as e:
            self._uow.rollback()
            return UnregisterPluginResult(
                success=False,
                errors=[{"code": "plugin.unregister_failed", "message": str(e), "path": "_global"}],
            )