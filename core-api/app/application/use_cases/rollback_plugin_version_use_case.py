# app/application/use_cases/plugi/rollback_plugin_version_use_case.py

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class RollbackPluginVersionResult:
    success: bool
    errors: List[Dict[str, Any]]


class RollbackPluginVersionUseCase:
    """
    Rollback troca:
      - App.version
      - AppManifest (manifest + checksum)
      - Rotas (replace total)
      - Permissões (replace total por module=plugin_id)
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str, target_version: str) -> RollbackPluginVersionResult:
        app = self._uow.plugin_repo.get_by_id(plugin_id)
        if not app:
            return RollbackPluginVersionResult(
                success=False,
                errors=[{"code": "plugin.not_found", "message": "Plugin not found", "path": "_global"}],
            )

        ver = self._uow.version_repo.get_version(plugin_id, target_version)
        if not ver:
            return RollbackPluginVersionResult(
                success=False,
                errors=[{"code": "plugin.version_not_found", "message": "Target version not found in history", "path": "version"}],
            )

        manifest = ver.get("manifest")
        checksum = ver.get("checksum")

        if not isinstance(manifest, dict):
            return RollbackPluginVersionResult(
                success=False,
                errors=[{"code": "plugin.invalid_version_manifest", "message": "Stored manifest is invalid", "path": "_global"}],
            )

        try:
            # version ativa
            self._uow.plugin_repo.update_version(plugin_id, target_version)

            # manifesto atual
            self._uow.manifest_repo.save(plugin_id, manifest, str(checksum or ""))

            # rotas: replace total
            self._uow.route_repo.delete_by_app(plugin_id)
            self._uow.route_repo.bulk_create([
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

            # permissões: replace total
            self._uow.permission_repo.delete_by_module(plugin_id)
            self._uow.permission_repo.bulk_create([
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
                errors=[{"code": "plugin.rollback_failed", "message": str(e), "path": "_global"}],
            )