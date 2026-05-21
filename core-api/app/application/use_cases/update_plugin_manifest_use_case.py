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
    Atualiza manifesto SEM alterar versão e SEM alterar estrutura do plugin.

    Permitido alterar apenas:
      - name
      - description
      - icon
      - label/icon/order/showInMenu das rotas

    Mudanças estruturais exigem nova versão e novo register.
    """

    def __init__(self, uow: UnitOfWork, validator: ManifestValidator):
        self._uow = uow
        self._validator = validator

    def execute(
        self,
        plugin_id: str,
        manifest: Dict[str, Any],
        *,
        actor_user_id: str | None = None,
        actor_email: str | None = None,
    ) -> UpdatePluginManifestResult:

        # ==========================================================
        # 1️⃣ Validação estrutural
        # ==========================================================

        validation = self._validator.validate(manifest)

        if not validation.is_valid:
            return UpdatePluginManifestResult(
                success=False,
                errors=[
                    {
                        "code": e.code,
                        "message": e.message,
                        "path": e.path
                    }
                    for e in validation.errors
                ],
            )

        # ==========================================================
        # 2️⃣ Valida ID
        # ==========================================================

        if str(manifest.get("id") or "") != plugin_id:
            return UpdatePluginManifestResult(
                success=False,
                errors=[
                    {
                        "code": "plugin.id_mismatch",
                        "message": "manifest.id deve ser igual ao plugin_id",
                        "path": "$.id"
                    }
                ],
            )

        plugin = self._uow.plugins.get_by_id(plugin_id)

        if not plugin:
            return UpdatePluginManifestResult(
                success=False,
                errors=[
                    {
                        "code": "plugin.not_found",
                        "message": "Plugin not found",
                        "path": "_global"
                    }
                ],
            )

        # ==========================================================
        # 3️⃣ Bloqueios estruturais
        # ==========================================================

        if str(manifest.get("version") or "") != str(plugin.version or ""):
            return UpdatePluginManifestResult(
                success=False,
                errors=[
                    {
                        "code": "plugin.version_change_not_allowed",
                        "message": "Alterar 'version' requer novo register do plugin.",
                        "path": "$.version"
                    }
                ],
            )

        if manifest.get("basePath") != plugin.base_path:
            return UpdatePluginManifestResult(
                success=False,
                errors=[
                    {
                        "code": "plugin.base_path_change_not_allowed",
                        "message": "Alterar basePath requer nova versão do plugin.",
                        "path": "$.basePath"
                    }
                ],
            )

        # ==========================================================
        # 4️⃣ Bloqueia alteração de permissões
        # ==========================================================

        existing_permissions = {
            p.code for p in self._uow.permissions.list_by_module(plugin_id)
        }

        manifest_permissions = {
            p.get("code")
            for p in (manifest.get("permissions") or [])
            if p.get("code")
        }

        if existing_permissions != manifest_permissions:
            return UpdatePluginManifestResult(
                success=False,
                errors=[
                    {
                        "code": "plugin.permission_change_not_allowed",
                        "message": "Alterar permissões requer nova versão do plugin.",
                        "path": "$.permissions"
                    }
                ],
            )

        # ==========================================================
        # 5️⃣ Bloqueia alteração estrutural de rotas
        # ==========================================================

        existing_routes = {
            r.path for r in self._uow.plugin_routes.list_by_app(plugin_id)
        }

        manifest_routes = {
            r.get("path")
            for r in (manifest.get("routes") or [])
            if r.get("path")
        }

        if existing_routes != manifest_routes:
            return UpdatePluginManifestResult(
                success=False,
                errors=[
                    {
                        "code": "plugin.route_structure_change_not_allowed",
                        "message": "Adicionar/remover rotas requer nova versão do plugin.",
                        "path": "$.routes"
                    }
                ],
            )

        # ==========================================================
        # 6️⃣ Atualiza metadata do plugin
        # ==========================================================

        self._uow.plugins.update_metadata(
            plugin_id,
            name=str(manifest.get("name") or plugin.name or ""),
            description=manifest.get("description"),
            icon=manifest.get("icon"),
            actor_user_id=actor_user_id,
            actor_email=actor_email,
        )

        # ==========================================================
        # 7️⃣ Atualiza manifest salvo
        # ==========================================================

        checksum = _checksum(manifest)

        self._uow.plugin_manifests.save(
            plugin_id,
            manifest,
            checksum
        )

        # ==========================================================
        # 8️⃣ Atualiza propriedades das rotas existentes
        # ==========================================================

        for route in (manifest.get("routes") or []):

            path = route.get("path")

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

        # ==========================================================
        # 9️⃣ Evento global
        # ==========================================================

        self._uow.collect_event(
            AdminChangedEvent(
                entity="plugins",
                action="plugin_manifest_updated",
                payload={
                    "pluginId": plugin_id,
                },
                target_user_id=None,
            )
        )

        return UpdatePluginManifestResult(success=True, errors=[])