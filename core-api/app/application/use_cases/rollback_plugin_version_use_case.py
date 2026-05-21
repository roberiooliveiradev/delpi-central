# app/application/use_cases/rollback_plugin_version_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List

from app.application.unit_of_work import UnitOfWork
from app.domain.events.admin_events import AdminChangedEvent


@dataclass(frozen=True)
class RollbackPluginVersionResult:
    success: bool
    errors: List[Dict[str, Any]]


class RollbackPluginVersionUseCase:

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(
        self,
        plugin_id: str,
        target_version: str,
        *,
        actor_user_id: str | None = None,
        actor_email: str | None = None,
    ) -> RollbackPluginVersionResult:

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

        # atualizar versão ativa
        self._uow.plugins.update_version(
            plugin_id,
            target_version,
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )

        self._uow.plugin_manifests.save(plugin_id, manifest, str(checksum or ""))

        # DELETE ordem correta
        self._uow.plugin_routes.delete_by_app(plugin_id)
        self._uow.plugin_permissions.delete_by_module(plugin_id)

        # CREATE ordem correta
        self._uow.plugin_permissions.bulk_create([
            {
                "code": p.get("code"),
                "name": p.get("name"),
                "description": p.get("description"),
                "module": plugin_id,
            }
            for p in (manifest.get("permissions") or [])
        ])

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

        self._uow.collect_event(
            AdminChangedEvent(
                entity="plugins",
                action="plugin_version_rolled_back",
                payload={
                    "pluginId": plugin_id,
                    "version": target_version,
                },
                actor_user_id=actor_user_id,
            )
        )

        return RollbackPluginVersionResult(success=True, errors=[])