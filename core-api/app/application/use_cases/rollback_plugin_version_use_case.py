# app/application/use_cases/rollback_plugin_version_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class RollbackPluginVersionResult:
    success: bool
    errors: List[Dict[str, Any]]


class RollbackPluginVersionUseCase:
    """
    Rollback troca:
      - versão ativa do plugin
      - manifesto
      - rotas (replace total)
      - permissões (replace total por module=plugin_id)
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str, target_version: str) -> RollbackPluginVersionResult:

        plugin = self._uow.plugins.get_by_id(plugin_id)
        if not plugin:
            return RollbackPluginVersionResult(
                success=False,
                errors=[{
                    "code": "plugin.not_found",
                    "message": "Plugin not found",
                    "path": "_global"
                }],
            )

        version = self._uow.plugin_versions.get_version(plugin_id, target_version)
        if not version:
            return RollbackPluginVersionResult(
                success=False,
                errors=[{
                    "code": "plugin.version_not_found",
                    "message": "Target version not found in history",
                    "path": "version"
                }],
            )

        manifest = version.get("manifest")
        checksum = version.get("checksum")

        if not isinstance(manifest, dict):
            return RollbackPluginVersionResult(
                success=False,
                errors=[{
                    "code": "plugin.invalid_version_manifest",
                    "message": "Stored manifest is invalid",
                    "path": "_global"
                }],
            )

        try:
            # Atualiza versão ativa
            self._uow.plugins.update_version(plugin_id, target_version)

            # Atualiza manifesto
            self._uow.plugin_manifests.save(plugin_id, manifest, str(checksum or ""))

            # Rotas: replace total
            self._uow.plugin_routes.delete_by_app(plugin_id)
            self._uow.plugin_routes.bulk_create([
                {
                    "app_id": plugin_id,
                    "path": r.get("path"),
                    "label": r.get("label"),
                    "icon": r.get("icon"),
                    "permission": r.get("permission"),
                    "order": r.get("order", 0),
                    "show_in_menu": r.get("showInMenu", True),
                }
                for r in (manifest.get("routes") or [])
            ])

            # Permissões: replace total
            self._uow.plugin_permissions.delete_by_module(plugin_id)
            self._uow.plugin_permissions.bulk_create([
                {
                    "code": p.get("code"),
                    "name": p.get("name"),
                    "description": p.get("description"),
                    "module": plugin_id,
                }
                for p in (manifest.get("permissions") or [])
            ])

            self._uow.commit()
            return RollbackPluginVersionResult(success=True, errors=[])

        except Exception as e:
            self._uow.rollback()
            return RollbackPluginVersionResult(
                success=False,
                errors=[{
                    "code": "plugin.rollback_failed",
                    "message": str(e),
                    "path": "_global"
                }],
            )