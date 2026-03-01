# app/application/use_cases/update_plugin_manifest_use_case.py

from dataclasses import dataclass
from typing import Dict, Any, List
import hashlib
import json

from app.application.unit_of_work import UnitOfWork
from app.application.validators.manifest_validator import ManifestValidator
from app.domain.events.admin_events import AdminChangedEvent


@dataclass(frozen=True)
class UpdatePluginManifestResult:
    success: bool
    errors: List[Dict[str, Any]]


def _checksum(manifest: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode("utf-8")
    ).hexdigest()


class UpdatePluginManifestUseCase:
    """
    Atualiza manifesto SEM alterar versão.
    """

    def __init__(self, uow: UnitOfWork, validator: ManifestValidator):
        self._uow = uow
        self._validator = validator

    def execute(self, plugin_id: str, manifest: Dict[str, Any]) -> UpdatePluginManifestResult:

        # 1️⃣ Validação estrutural
        validation = self._validator.validate(manifest)
        if not validation.is_valid:
            return UpdatePluginManifestResult(
                success=False,
                errors=[{
                    "code": e.code,
                    "message": e.message,
                    "path": e.path
                } for e in validation.errors],
            )

        # 2️⃣ Valida ID
        if str(manifest.get("id") or "") != plugin_id:
            return UpdatePluginManifestResult(
                success=False,
                errors=[{
                    "code": "plugin.id_mismatch",
                    "message": "manifest.id deve ser igual ao plugin_id",
                    "path": "$.id"
                }],
            )

        plugin = self._uow.plugins.get_by_id(plugin_id)
        if not plugin:
            return UpdatePluginManifestResult(
                success=False,
                errors=[{
                    "code": "plugin.not_found",
                    "message": "Plugin not found",
                    "path": "_global"
                }],
            )

        # 3️⃣ Não permite alterar versão
        if str(manifest.get("version") or "") != str(plugin.version or ""):
            return UpdatePluginManifestResult(
                success=False,
                errors=[{
                    "code": "plugin.version_change_not_allowed",
                    "message": "Não é permitido alterar 'version' via update.",
                    "path": "$.version"
                }],
            )

        # 4️⃣ Regra de negócio (transacional)

        self._uow.plugins.update_metadata(
            plugin_id,
            name=str(manifest.get("name") or plugin.name or ""),
            description=manifest.get("description"),
            icon=manifest.get("icon"),
        )

        checksum = _checksum(manifest)
        self._uow.plugin_manifests.save(plugin_id, manifest, checksum)

        for route in (manifest.get("routes") or []):
            path = (route or {}).get("path")
            if not path:
                continue

            patch = {
                "label": route.get("label"),
                "icon": route.get("icon"),
                "order": route.get("order"),
            }

            if "showInMenu" in route:
                patch["show_in_menu"] = route.get("showInMenu")

            self._uow.plugin_routes.update_by_app_and_path(
                plugin_id,
                str(path),
                patch
            )

        # 5️⃣ Evento global
        self._uow.collect_event(
            AdminChangedEvent(
                entity="plugins",
                action="plugin_manifest_updated",
                payload={
                    "pluginId": plugin_id,
                },
                target_user_id=None,  # broadcast
            )
        )

        return UpdatePluginManifestResult(success=True, errors=[])