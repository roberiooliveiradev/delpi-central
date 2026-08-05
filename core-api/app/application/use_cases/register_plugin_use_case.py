# app/application/use_cases/register_plugin_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List
import hashlib
import json

from app.application.unit_of_work import UnitOfWork
from app.application.validators.manifest_validator import ManifestValidator
from app.domain.events.admin_events import AdminChangedEvent
from app.domain.services.plugin_permission_sync_service import PluginPermissionSyncService


@dataclass(frozen=True)
class RegisterResult:
    success: bool
    errors: List[Dict[str, Any]]


def _checksum(manifest: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _route_row(plugin_id: str, route: Dict[str, Any]) -> Dict[str, Any]:
    show_in_menu = route.get("showInMenu")
    if show_in_menu is None:
        show_in_menu = route.get("show_in_menu", True)

    return {
        "app_id": plugin_id,
        "path": route.get("path"),
        "label": route.get("label"),
        "icon": route.get("icon"),
        "permission": route.get("permission"),
        "order": route.get("order", 0),
        "show_in_menu": True if show_in_menu is None else bool(show_in_menu),
    }


class RegisterPluginUseCase:

    def __init__(self, uow: UnitOfWork, validator: ManifestValidator):
        self._uow = uow
        self._validator = validator

    def execute(
        self,
        manifest: Dict[str, Any],
        *,
        actor_user_id: str | None = None,
        actor_name: str | None = None,
    ) -> RegisterResult:

        validation = self._validator.validate(manifest)

        if not validation.is_valid:
            return RegisterResult(
                success=False,
                errors=[
                    {"code": e.code, "message": e.message, "path": e.path}
                    for e in validation.errors
                ],
            )

        plugin_id = manifest["id"]
        version = manifest["version"]

        base_path = manifest.get("basePath") or manifest.get("base_path")

        if not base_path:
            return RegisterResult(
                False,
                [{
                    "code": "validation_error",
                    "message": "basePath é obrigatório",
                    "path": "basePath",
                }],
            )

        plugin = self._uow.plugins.get_by_id(plugin_id)
        checksum = _checksum(manifest)

        # =====================================================
        # PLUGIN NÃO EXISTE → CRIA
        # =====================================================

        if not plugin:

            self._uow.plugins.create(
                {
                    "id": plugin_id,
                    "name": manifest["name"],
                    "description": manifest.get("description"),
                    "base_path": base_path,
                    "icon": manifest.get("icon"),
                    "type": manifest.get("type"),
                    "version": version,
                    "active": True,
                },
                actor_user_id=actor_user_id,
                actor_name=actor_name,
            )

            self._uow.plugin_manifests.save(plugin_id, manifest, checksum)

            self._uow.plugin_versions.create({
                "app_id": plugin_id,
                "version": version,
                "manifest": manifest,
                "checksum": checksum,
            })

            # permissions first (module always = plugin_id), then routes
            desired = PluginPermissionSyncService.normalize_desired(
                plugin_id,
                manifest.get("permissions"),
            )
            self._uow.plugin_permissions.sync_module(plugin_id, desired)

            self._uow.plugin_routes.bulk_create([
                _route_row(plugin_id, route)
                for route in (manifest.get("routes") or [])
            ])

        # =====================================================
        # PLUGIN EXISTE → NOVA VERSÃO
        # =====================================================

        else:

            if self._uow.plugin_versions.exists(plugin_id, version):
                return RegisterResult(
                    success=False,
                    errors=[{
                        "code": "plugin.version_already_exists",
                        "message": "Esta versão já está registrada",
                        "path": "version",
                    }],
                )

            self._uow.plugins.update_version(
                plugin_id,
                version,
                actor_user_id=actor_user_id,
                actor_name=actor_name,
            )

            self._uow.plugin_manifests.save(plugin_id, manifest, checksum)

            self._uow.plugin_versions.create({
                "app_id": plugin_id,
                "version": version,
                "manifest": manifest,
                "checksum": checksum,
            })

            # Rotas dependem de permission_id: apagar rotas, sync perms (UUID estável), recriar rotas
            self._uow.plugin_routes.delete_by_app(plugin_id)

            desired = PluginPermissionSyncService.normalize_desired(
                plugin_id,
                manifest.get("permissions"),
            )
            self._uow.plugin_permissions.sync_module(plugin_id, desired)

            self._uow.plugin_routes.bulk_create([
                _route_row(plugin_id, r)
                for r in (manifest.get("routes") or [])
            ])

        self._uow.collect_event(
            AdminChangedEvent(
                entity="plugins",
                action="plugin_registered",
                payload={
                    "pluginId": plugin_id,
                    "version": version,
                },
                actor_user_id=actor_user_id,
            )
        )

        return RegisterResult(success=True, errors=[])