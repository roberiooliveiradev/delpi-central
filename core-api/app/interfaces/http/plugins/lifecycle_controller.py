# app/interfaces/http/plugins/lifecycle_controller.py

from flask import Blueprint, request, jsonify, g

from app.infrastructure.plugins.unit_of_work import SqlAlchemyUnitOfWork
from app.application.plugins.register_plugin import RegisterPluginUseCase
from app.application.plugins.update_plugin_manifest import UpdatePluginManifestUseCase
from app.application.plugins.manifest_validator import ManifestValidator
from app.infrastructure.db.models import AppManifest

plugins_bp = Blueprint(
    "plugins_lifecycle",
    __name__,
    url_prefix="/core-api/plugins"
)


def require_apps_manage():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user.is_superadmin:
        return None
    return jsonify({"error": "Forbidden"}), 403


@plugins_bp.get("/<plugin_id>/manifest")
def get_manifest(plugin_id: str):
    guard = require_apps_manage()
    if guard:
        return guard

    row = AppManifest.query.filter_by(app_id=plugin_id).first()
    if not row:
        return jsonify({"error": "Manifest not found"}), 404

    return jsonify(row.manifest)


@plugins_bp.post("/register")
def register_plugin():
    guard = require_apps_manage()
    if guard:
        return guard

    manifest = request.get_json(silent=True)
    if not isinstance(manifest, dict):
        return jsonify({"error": "Body deve ser JSON"}), 400

    user = g.current_user
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    uow = SqlAlchemyUnitOfWork()
    validator = ManifestValidator()
    use_case = RegisterPluginUseCase(uow, validator)

    result = use_case.execute(
        manifest=manifest,
        user_id=str(user.id),
        user_ip=ip,
    )

    if not result.success:
        return jsonify({
            "errors": [
                {
                    "code": e.code,
                    "message": e.message,
                    "path": getattr(e, "path", "_global"),
                }
                for e in result.errors
            ]
        }), 400

    return jsonify({
        "status": "registered",
        "appId": manifest["id"],
        "version": manifest["version"],
    }), 201


@plugins_bp.put("/<plugin_id>/manifest")
def update_manifest(plugin_id: str):
    guard = require_apps_manage()
    if guard:
        return guard

    manifest = request.get_json(silent=True)
    if not isinstance(manifest, dict):
        return jsonify({"error": "Body deve ser JSON"}), 400

    validator = ManifestValidator()
    use_case = UpdatePluginManifestUseCase(validator)

    result = use_case.execute(plugin_id=plugin_id, manifest=manifest)

    if not result.success:
        return jsonify({"errors": result.errors}), 400

    return jsonify({"ok": True}), 200