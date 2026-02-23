# app/interfaces/http/plugins_controller.py

from flask import Blueprint, request, jsonify, g

from app.infrastructure.plugins.unit_of_work import SqlAlchemyUnitOfWork
from app.application.plugins.register_plugin import RegisterPluginUseCase
from app.application.plugins.manifest_validator import ManifestValidator
from app.infrastructure.db.models import App, AppManifest

plugins_bp = Blueprint("plugins", __name__, url_prefix="/core-api/plugins")


# =========================================================
# UTIL
# =========================================================

def require_apps_manage():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if user.is_superadmin:
        return None
    if "apps.manage" not in getattr(user, "permissions", []):
        return jsonify({"error": "Forbidden"}), 403
    return None


def _normalize_error_path(path: str | None) -> str:
    """
    Converte:
      $.routes[0].path  -> routes[0].path
      $.basePath        -> basePath
      $                 -> _global
      None              -> _global
    """
    if not path:
        return "_global"

    p = str(path).strip()
    if not p or p == "$":
        return "_global"

    # remove prefixo JSONPath "$." ou "$"
    if p.startswith("$."):
        p = p[2:]
    elif p.startswith("$"):
        p = p[1:]
        if p.startswith("."):
            p = p[1:]

    return p or "_global"


# =========================================================
# GET PLUGIN (Manifesto)
# =========================================================

@plugins_bp.route("/<plugin_id>/manifest", methods=["GET"])
def get_plugin_manifest(plugin_id: str):
    guard = require_apps_manage()
    if guard:
        return guard

    row = AppManifest.query.filter_by(app_id=plugin_id).first()
    if not row:
        return jsonify({"error": "Manifest not found"}), 404

    return jsonify(row.manifest), 200


# =========================================================
# REGISTER PLUGIN (Manifesto)
# =========================================================

@plugins_bp.route("/register", methods=["POST"])
def register_plugin():
    guard = require_apps_manage()
    if guard:
        return guard

    manifest = request.get_json(silent=True)
    if not isinstance(manifest, dict):
        return jsonify({"error": "Body deve ser JSON"}), 400

    user = g.current_user
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

    uow = SqlAlchemyUnitOfWork()
    validator = ManifestValidator()
    use_case = RegisterPluginUseCase(uow, validator)

    result = use_case.execute(
        manifest=manifest,
        user_id=str(user.id),
        user_ip=ip_address,
    )

    if not result.success:
        return jsonify({
            "errors": [
                {
                    "code": e.code,
                    "message": e.message,
                    "path": _normalize_error_path(getattr(e, "path", None)),
                }
                for e in result.errors
            ]
        }), 400

    return jsonify({
        "status": "registered",
        "appId": manifest["id"],
        "version": manifest["version"],
    }), 201