# app/application/plugins/register_plugin.py

import hashlib
import json
from dataclasses import dataclass
from typing import Dict, Any, List

from app.application.plugins.manifest_validator import ManifestValidator
from app.application.plugins.ports import UnitOfWork
from app.domain.plugins.manifest_rules import ManifestError


@dataclass(frozen=True)
class RegisterPluginResult:
    success: bool
    errors: List[ManifestError]


class RegisterPluginUseCase:

    def __init__(self, uow: UnitOfWork, validator: ManifestValidator):
        self._uow = uow
        self._validator = validator

    # ==========================================================
    # EXECUTE
    # ==========================================================

    def execute(
        self,
        manifest: Dict[str, Any],
        user_id: str,
        user_ip: str,
    ) -> RegisterPluginResult:

        validation = self._validator.validate(manifest)

        if not validation.is_valid:
            return RegisterPluginResult(False, validation.errors)

        app_id = manifest["id"]
        version = manifest["version"]

        try:
            version_error = self._handle_app_version(app_id, version, manifest)
            if version_error:
                self._uow.rollback()
                return RegisterPluginResult(False, [version_error])

            permission_error = self._handle_permissions(app_id, manifest)
            if permission_error:
                self._uow.rollback()
                return RegisterPluginResult(False, [permission_error])

            route_error = self._handle_routes(app_id, manifest)
            if route_error:
                self._uow.rollback()
                return RegisterPluginResult(False, [route_error])

            # 🔥 salvar snapshot atual
            self._save_manifest(app_id, manifest)

            # 🔥 salvar histórico de versão
            version_error = self._save_version_history(app_id, version, manifest)
            if version_error:
                self._uow.rollback()
                return RegisterPluginResult(False, [version_error])

            self._audit(app_id, version, user_id, user_ip)

            self._uow.commit()

            from app.infrastructure.security.rbac_cache import rbac_cache
            rbac_cache.clear()

            return RegisterPluginResult(True, [])

        except Exception:
            self._uow.rollback()
            raise

    # ==========================================================
    # VERSION HISTORY
    # ==========================================================

    def _save_version_history(
        self,
        app_id: str,
        version: str,
        manifest: Dict[str, Any],
    ) -> ManifestError | None:

        checksum = hashlib.sha256(
            json.dumps(manifest, sort_keys=True).encode()
        ).hexdigest()

        # 🔒 Bloqueia duplicidade elegante
        if self._uow.app_version_repo.exists(app_id, version):
            return ManifestError(
                code="version_already_registered",
                message=f"Version '{version}' already registered for app '{app_id}'.",
                path="$.version",
            )

        self._uow.app_version_repo.create({
            "app_id": app_id,
            "version": version,
            "manifest": manifest,
            "checksum": checksum,
        })

        return None

    # ==========================================================
    # APP + VERSION
    # ==========================================================

    def _handle_app_version(
        self,
        app_id: str,
        version: str,
        manifest: Dict[str, Any],
    ) -> ManifestError | None:

        existing_app = self._uow.app_repo.get_by_id(app_id)

        if existing_app:

            current_version = existing_app["version"]

            if not self._is_upgrade_allowed(current_version, version):
                return ManifestError(
                    code="version_upgrade_not_allowed",
                    message=f"Upgrade not allowed: {current_version} → {version}",
                    path="$.version",
                )

            self._uow.app_repo.update_version(app_id, version)
            return None

        # Novo app
        self._uow.app_repo.create(
            {
                "id": app_id,
                "name": manifest["name"],
                "description": manifest.get("description"),
                "base_path": manifest["basePath"],
                "icon": manifest.get("icon"),
                "type": manifest["type"],
                "version": version,
                "active": True,
            }
        )

        return None

    # ==========================================================
    # PERMISSIONS
    # ==========================================================

    def _handle_permissions(
        self,
        app_id: str,
        manifest: Dict[str, Any],
    ) -> ManifestError | None:

        new_permissions = []

        for perm in manifest["permissions"]:

            existing = self._uow.permission_repo.get_by_code(perm["code"])

            if not existing:
                new_permissions.append(perm)
                continue

            if existing.module != app_id:
                return ManifestError(
                    code="permission_code_collision",
                    message=f"Permission '{perm['code']}' belongs to module '{existing.module}'.",
                    path="$.permissions",
                )

        if new_permissions:
            self._uow.permission_repo.bulk_create(
                [
                    {
                        "code": p["code"],
                        "name": p["name"],
                        "description": p.get("description"),
                        "module": p.get("module"),
                    }
                    for p in new_permissions
                ]
            )

        return None

    # ==========================================================
    # ROUTES
    # ==========================================================

    def _handle_routes(
        self,
        app_id: str,
        manifest: Dict[str, Any],
    ) -> ManifestError | None:

        new_routes = []

        for route in manifest["routes"]:

            existing_route = self._uow.route_repo.get_by_path(route["path"])

            if existing_route:

                if existing_route.app_id != app_id:
                    return ManifestError(
                        code="route_path_collision",
                        message=f"Route path already exists: {route['path']}",
                        path="$.routes",
                    )

                continue

            new_routes.append(route)

        if new_routes:
            self._uow.route_repo.bulk_create(
                [
                    {
                        "app_id": app_id,
                        "path": r["path"],
                        "label": r.get("label"),
                        "icon": r.get("icon"),
                        "permission": r["permission"],
                        "show_in_menu": r.get("showInMenu", True),
                        "order": r.get("order", 0),
                    }
                    for r in new_routes
                ]
            )

        return None

    # ==========================================================
    # MANIFEST
    # ==========================================================

    def _save_manifest(self, app_id: str, manifest: Dict[str, Any]) -> None:

        checksum = hashlib.sha256(
            json.dumps(manifest, sort_keys=True).encode()
        ).hexdigest()

        self._uow.manifest_repo.save(app_id, manifest, checksum)

    # ==========================================================
    # AUDIT
    # ==========================================================

    def _audit(
        self,
        app_id: str,
        version: str,
        user_id: str,
        user_ip: str,
    ) -> None:

        self._uow.audit_repo.log(
            {
                "user_id": user_id,
                "action": "plugin_registered",
                "entity_type": "plugin",
                "entity_id": app_id,
                "payload": {"version": version},
                "ip_address": user_ip,
            }
        )

    # ==========================================================
    # VERSION RULE
    # ==========================================================

    def _is_upgrade_allowed(self, current: str, new: str) -> bool:

        current_parts = list(map(int, current.split(".")))
        new_parts = list(map(int, new.split(".")))

        if new_parts < current_parts:
            return False

        if new_parts[0] > current_parts[0]:
            return False

        return True