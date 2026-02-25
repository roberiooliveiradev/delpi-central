# app/application/use_cases/update_plugin_manifest_use_case.py

from dataclasses import dataclass
from typing import Any, Dict, List
import hashlib
import json

from app.application.unit_of_work import UnitOfWork
from app.application.validators.manifest_validator import ManifestValidator


@dataclass(frozen=True)
class UpdatePluginManifestResult:
    success: bool
    errors: List[Dict[str, Any]]


def _checksum(manifest: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()


class UpdatePluginManifestUseCase:
    """
    Atualiza manifesto do plugin SEM alterar versão.
    Regra: upgrade = register (nova versão) / rollback = rollback endpoint.
    """

    def __init__(self, uow: UnitOfWork, validator: ManifestValidator):
        self._uow = uow
        self._validator = validator

    def execute(self, plugin_id: str, manifest: Dict[str, Any]) -> UpdatePluginManifestResult:
        validation = self._validator.validate(manifest)
        if not validation.is_valid:
            return UpdatePluginManifestResult(
                success=False,
                errors=[{"code": e.code, "message": e.message, "path": e.path} for e in validation.errors],
            )

        if str(manifest.get("id") or "") != plugin_id:
            return UpdatePluginManifestResult(
                success=False,
                errors=[{
                    "code": "plugin.id_mismatch",
                    "message": "manifest.id deve ser igual ao plugin_id da URL",
                    "path": "$.id",
                }],
            )

        app = self._uow.plugin_repo.get_by_id(plugin_id)
        if not app:
            return UpdatePluginManifestResult(
                success=False,
                errors=[{"code": "plugin.not_found", "message": "Plugin not found", "path": "_global"}],
            )

        if str(manifest.get("version") or "") != str(app.get("version") or ""):
            return UpdatePluginManifestResult(
                success=False,
                errors=[{
                    "code": "plugin.version_change_not_allowed",
                    "message": "Não é permitido alterar 'version' via update. Use register (upgrade) ou rollback.",
                    "path": "$.version",
                }],
            )

        try:
            # Atualiza metadados do App
            self._uow.plugin_repo.update_metadata(
                plugin_id,
                name=str(manifest.get("name") or app.get("name") or ""),
                description=manifest.get("description"),
                icon=manifest.get("icon"),
            )

            # Atualiza manifesto + checksum
            cs = _checksum(manifest)
            self._uow.manifest_repo.save(plugin_id, manifest, cs)

            # Atualiza APENAS rotas existentes (edit-only): não cria novas rotas aqui.
            # Isso evita "burlar governança" via update.
            for r in (manifest.get("routes") or []):
                path = (r or {}).get("path")
                if not path:
                    continue

                patch: Dict[str, Any] = {
                    "label": (r or {}).get("label"),
                    "icon": (r or {}).get("icon"),
                    "order": (r or {}).get("order"),
                }
                if "showInMenu" in (r or {}):
                    patch["show_in_menu"] = (r or {}).get("showInMenu")

                self._uow.route_repo.update_by_app_and_path(plugin_id, str(path), patch)

            self._uow.commit()
            return UpdatePluginManifestResult(success=True, errors=[])

        except Exception as e:
            self._uow.rollback()
            return UpdatePluginManifestResult(
                success=False,
                errors=[{"code": "plugin.update_failed", "message": str(e), "path": "_global"}],
            )