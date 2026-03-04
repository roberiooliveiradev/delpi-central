# app/application/use_cases/register_plugin_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List
import hashlib
import json

from app.application.unit_of_work import UnitOfWork
from app.application.validators.manifest_validator import ManifestValidator
from app.domain.events.admin_events import AdminChangedEvent


@dataclass(frozen=True)
class RegisterResult:
    success: bool
    errors: List[Dict[str, Any]]


def _checksum(manifest: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode("utf-8")
    ).hexdigest()


class RegisterPluginUseCase:

    def __init__(self, uow: UnitOfWork, validator: ManifestValidator):
        self._uow = uow
        self._validator = validator

    def execute(self, manifest: Dict[str, Any]) -> RegisterResult:

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
                    "message": "basePath is required",
                    "path": "$.basePath",
                }],
            )

        plugin = self._uow.plugins.get_by_id(plugin_id)
        checksum = _checksum(manifest)

        # =====================================================
        # PLUGIN NÃO EXISTE → CRIA
        # =====================================================

        if not plugin:

            self._uow.plugins.create({
                "id": plugin_id,
                "name": manifest["name"],
                "description": manifest.get("description"),
                "base_path": base_path,
                "icon": manifest.get("icon"),
                "type": manifest.get("type"),
                "version": version,
                "active": True,
            })

            self._uow.plugin_manifests.save(plugin_id, manifest, checksum)

            self._uow.plugin_versions.create({
                "app_id": plugin_id,
                "version": version,
                "manifest": manifest,
                "checksum": checksum,
            })

            # create permissions first
            self._uow.plugin_permissions.bulk_create(
                manifest.get("permissions", [])
            )

            # then routes
            self._uow.plugin_routes.bulk_create([
                {"app_id": plugin_id, **route}
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
                        "message": "This version is already registered",
                        "path": "$.version",
                    }],
                )

            self._uow.plugins.update_version(plugin_id, version)

            self._uow.plugin_manifests.save(plugin_id, manifest, checksum)

            self._uow.plugin_versions.create({
                "app_id": plugin_id,
                "version": version,
                "manifest": manifest,
                "checksum": checksum,
            })

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
                action="plugin_registered",
                payload={
                    "pluginId": plugin_id,
                    "version": version,
                },
                target_user_id=None,
            )
        )

        return RegisterResult(success=True, errors=[])