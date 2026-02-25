# app/application/use_cases/register_plugin_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List
import hashlib
import json

from app.application.unit_of_work import UnitOfWork
from app.application.validators.manifest_validator import ManifestValidator


@dataclass(frozen=True)
class RegisterResult:
    success: bool
    errors: List[Dict[str, Any]]


class RegisterPluginUseCase:

    def __init__(self, uow: UnitOfWork, validator: ManifestValidator):
        self._uow = uow
        self._validator = validator

    def execute(self, manifest: Dict[str, Any]) -> RegisterResult:

        validation = self._validator.validate(manifest)
        if not validation.is_valid:
            return RegisterResult(False, [
                {"code": e.code, "message": e.message, "path": e.path}
                for e in validation.errors
            ])

        plugin_id = manifest["id"]
        version = manifest["version"]

        if self._uow.plugins.get_by_id(plugin_id):
            return RegisterResult(False, [{
                "code": "plugin.already_exists",
                "message": "Plugin already registered",
                "path": "id"
            }])

        try:
            self._uow.plugins.create({
                "id": plugin_id,
                "name": manifest["name"],
                "description": manifest.get("description"),
                "icon": manifest.get("icon"),
                "type": manifest.get("type"),
                "version": version,
                "active": True,
            })

            checksum = hashlib.sha256(
                json.dumps(manifest, sort_keys=True).encode()
            ).hexdigest()

            self._uow.plugin_manifests.save(plugin_id, manifest, checksum)

            self._uow.plugin_versions.create({
                "app_id": plugin_id,
                "version": version,
                "manifest": manifest,
                "checksum": checksum,
            })

            self._uow.plugin_permissions.bulk_create(manifest.get("permissions", []))

            self._uow.plugin_routes.bulk_create([
                {"app_id": plugin_id, **route}
                for route in manifest.get("routes", [])
            ])

            self._uow.commit()
            return RegisterResult(True, [])

        except Exception as e:
            self._uow.rollback()
            return RegisterResult(False, [{
                "code": "plugin.register_failed",
                "message": str(e),
                "path": "_global"
            }])