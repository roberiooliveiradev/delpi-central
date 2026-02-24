# app/interfaces/http/plugins/lifecycle_controller.py

from flask import Blueprint, request, jsonify, g

from app.infrastructure.plugins.unit_of_work import SqlAlchemyUnitOfWork
from app.application.plugins.register_plugin import RegisterPluginUseCase
from app.application.plugins.update_plugin_manifest import UpdatePluginManifestUseCase
from app.application.plugins.manifest_validator import ManifestValidator
from app.infrastructure.db.models import AppManifest, AppVersion
from app.application.plugins.rollback_plugin_version import RollbackPluginVersionUseCase
from app.domain.services.admin_event_service import emit_admin_event


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
    
    emit_admin_event("plugins", "register", {
        "appId": manifest["id"],
        "version": manifest["version"],
    })
    
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
    
    emit_admin_event("plugins", "manifest_update", {
        "appId": plugin_id,
    })
    
    return jsonify({"ok": True}), 200


@plugins_bp.get("/<plugin_id>/versions")
def list_versions(plugin_id: str):
    guard = require_apps_manage()
    if guard:
        return guard

    rows = AppVersion.query.filter_by(app_id=plugin_id)\
        .order_by(AppVersion.created_at.desc())\
        .all()

    return jsonify([
        {
            "version": r.version,
            "checksum": r.checksum,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ])


@plugins_bp.post("/<plugin_id>/rollback")
def rollback_plugin(plugin_id: str):
    guard = require_apps_manage()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}
    target_version = data.get("version")

    if not target_version:
        return jsonify({
            "error": "version is required"
        }), 400

    use_case = RollbackPluginVersionUseCase()
    result = use_case.execute(plugin_id, target_version)

    if not result.success:
        return jsonify({"errors": result.errors}), 400

    emit_admin_event("plugins", "rollback", {
        "appId": plugin_id,
        "version": target_version,
    })

    return jsonify({
        "status": "rolled_back",
        "version": target_version,
    }), 200