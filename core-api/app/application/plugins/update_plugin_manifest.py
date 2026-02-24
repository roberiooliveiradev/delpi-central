# app/application/plugins/update_plugin_manifest.py

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.infrastructure.db.models import App, AppRoute, AppManifest, Permission
from app.extensions.db import db


@dataclass
class UpdateResult:
    success: bool
    errors: List[dict]


class UpdatePluginManifestUseCase:
    def __init__(self, validator):
        self.validator = validator

    def execute(self, plugin_id: str, manifest: Dict[str, Any]) -> UpdateResult:
        # 🔎 1) Validação (schema + rules)
        validation = self.validator.validate(manifest)

        if not validation.is_valid:
            return UpdateResult(
                success=False,
                errors=[
                    {
                        "code": e.code,
                        "message": e.message,
                        "path": getattr(e, "path", "_global"),
                    }
                    for e in validation.errors
                ],
            )

        # 🔎 2) Garantir que ID do manifest bate com URL
        if manifest.get("id") != plugin_id:
            return UpdateResult(
                success=False,
                errors=[{
                    "code": "plugin.id_mismatch",
                    "message": "manifest.id deve ser igual ao plugin_id da URL",
                    "path": "id",
                }],
            )

        # 🔎 3) Buscar App
        app = App.query.filter_by(id=plugin_id).first()
        if not app:
            return UpdateResult(
                success=False,
                errors=[{
                    "code": "plugin.not_found",
                    "message": "App não encontrada para este plugin",
                    "path": "_global",
                }],
            )

        # =========================================================
        # 🔥 Atualiza metadados do App (campos mutáveis)
        # =========================================================

        app.name = manifest.get("name") or app.name
        app.description = manifest.get("description")
        app.icon = manifest.get("icon")

        # =========================================================
        # 🔥 Atualiza manifest salvo (fonte de verdade)
        # =========================================================

        row = AppManifest.query.filter_by(app_id=plugin_id).first()

        if not row:
            row = AppManifest(app_id=plugin_id, manifest=manifest)
            db.session.add(row)
        else:
            row.manifest = manifest

        # =========================================================
        # 🔥 Sincroniza metadados das rotas existentes
        # =========================================================

        routes_payload = manifest.get("routes") or []

        # cria mapa por path (chave estável)
        payload_by_path = {
            r.get("path"): r
            for r in routes_payload
            if r.get("path")
        }

        db_routes = AppRoute.query.filter_by(app_id=plugin_id).all()
        db_by_path = {r.path: r for r in db_routes}

        for path, rjson in payload_by_path.items():
            rdb = db_by_path.get(path)
            if not rdb:
                # 🔒 Não cria novas rotas via edit
                # (governança fica com register/upgrade)
                continue

            rdb.label = rjson.get("label")
            rdb.icon = rjson.get("icon")
            rdb.order = rjson.get("order")

            # manifesto usa showInMenu
            if "showInMenu" in rjson:
                rdb.show_in_menu = rjson.get("showInMenu")

        # =========================================================
        # 💾 Commit
        # =========================================================

        db.session.commit()

        return UpdateResult(success=True, errors=[])