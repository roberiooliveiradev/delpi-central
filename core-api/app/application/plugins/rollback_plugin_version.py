# app/application/plugins/rollback_plugin_version.py

from dataclasses import dataclass
from typing import List, Dict, Any

from app.infrastructure.db.models import (
    App,
    AppManifest,
    AppRoute,
    Permission,
    AppVersion,
)
from app.extensions.db import db


@dataclass
class RollbackResult:
    success: bool
    errors: List[Dict[str, Any]]


class RollbackPluginVersionUseCase:

    def execute(self, plugin_id: str, target_version: str) -> RollbackResult:

        app = App.query.filter_by(id=plugin_id).first()
        if not app:
            return RollbackResult(False, [{
                "code": "plugin.not_found",
                "message": "Plugin not found",
                "path": "_global",
            }])

        version_row = AppVersion.query.filter_by(
            app_id=plugin_id,
            version=target_version
        ).first()

        if not version_row:
            return RollbackResult(False, [{
                "code": "plugin.version_not_found",
                "message": "Target version not found in history",
                "path": "version",
            }])

        manifest = version_row.manifest

        try:
            # ===============================
            # 🔥 Atualiza versão ativa
            # ===============================
            app.version = target_version

            # ===============================
            # 🔥 Atualiza manifest atual
            # ===============================
            current_manifest = AppManifest.query.filter_by(app_id=plugin_id).first()

            if not current_manifest:
                current_manifest = AppManifest(
                    app_id=plugin_id,
                    manifest=manifest,
                    checksum=version_row.checksum,
                )
                db.session.add(current_manifest)
            else:
                current_manifest.manifest = manifest
                current_manifest.checksum = version_row.checksum

            # ===============================
            # 🔥 Sincroniza rotas
            # ===============================
            AppRoute.query.filter_by(app_id=plugin_id).delete()

            for route in manifest.get("routes", []):
                db.session.add(AppRoute(
                    app_id=plugin_id,
                    path=route["path"],
                    label=route.get("label"),
                    icon=route.get("icon"),
                    order=route.get("order"),
                    show_in_menu=route.get("showInMenu", True),
                ))

            # ===============================
            # 🔥 Sincroniza permissões
            # ===============================
            Permission.query.filter_by(module=plugin_id).delete()

            for perm in manifest.get("permissions", []):
                db.session.add(Permission(
                    code=perm["code"],
                    name=perm["name"],
                    description=perm.get("description"),
                    module=plugin_id,
                ))

            db.session.commit()

            return RollbackResult(True, [])

        except Exception as e:
            db.session.rollback()
            raise