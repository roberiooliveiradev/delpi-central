# app/interfaces/http/plugins_controller.py

from flask import Blueprint, request, jsonify, g

from app.infrastructure.plugins.unit_of_work import SqlAlchemyUnitOfWork
from app.application.plugins.register_plugin import RegisterPluginUseCase
from app.application.plugins.manifest_validator import ManifestValidator
from app.infrastructure.db.models import App

plugins_bp = Blueprint(
    "plugins",
    __name__,
    url_prefix="/core-api/plugins"
)


# =========================================================
# UTIL
# =========================================================

def require_superadmin():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if not getattr(user, "is_superadmin", False):
        return jsonify({"error": "Forbidden"}), 403
    return None

def require_apps_manage():
    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    if user.is_superadmin:
        return None

    if "apps.manage" not in getattr(user, "permissions", []):
        return jsonify({"error": "Forbidden"}), 403

    return None

# =========================================================
# REGISTER PLUGIN (Manifesto)
# =========================================================

@plugins_bp.route("/register", methods=["POST"])
def register_plugin():

    guard= require_apps_manage()
    if guard:
        return guard

    manifest = request.get_json(silent=True)
    if not isinstance(manifest, dict):
        return jsonify({"error": "Body deve ser JSON"}), 400

    user = g.current_user
    ip_address = request.headers.get(
        "X-Forwarded-For",
        request.remote_addr
    )

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
                    "path": e.path
                }
                for e in result.errors
            ]
        }), 400

    return jsonify({
        "status": "registered",
        "appId": manifest["id"],
        "version": manifest["version"]
    }), 201


# =========================================================
# LIST PLUGINS
# =========================================================

@plugins_bp.route("", methods=["GET"])
def list_plugins():

    guard= require_apps_manage()
    if guard:
        return guard

    rows = App.query.order_by(App.name.asc()).all()

    return jsonify([
        {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "base_path": a.base_path,
            "icon": a.icon,
            "type": a.type,
            "version": a.version,
            "active": a.active,
        }
        for a in rows
    ])


# =========================================================
# GET PLUGIN DETAIL
# =========================================================

@plugins_bp.route("/<plugin_id>", methods=["GET"])
def get_plugin(plugin_id):

    guard= require_apps_manage()
    if guard:
        return guard

    app = App.query.get(plugin_id)
    if not app:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "id": app.id,
        "name": app.name,
        "description": app.description,
        "base_path": app.base_path,
        "icon": app.icon,
        "type": app.type,
        "version": app.version,
        "active": app.active,
    })


# =========================================================
# ACTIVATE / DEACTIVATE
# =========================================================

@plugins_bp.route("/<plugin_id>/activate", methods=["PUT"])
def activate_plugin(plugin_id):

    guard= require_apps_manage()
    if guard:
        return guard

    app = App.query.get(plugin_id)
    if not app:
        return jsonify({"error": "Not found"}), 404

    app.active = True
    from app.extensions.db import db
    db.session.commit()

    return jsonify({"ok": True})


@plugins_bp.route("/<plugin_id>/deactivate", methods=["PUT"])
def deactivate_plugin(plugin_id):

    guard= require_apps_manage()
    if guard:
        return guard

    app = App.query.get(plugin_id)
    if not app:
        return jsonify({"error": "Not found"}), 404

    app.active = False
    from app.extensions.db import db
    db.session.commit()

    return jsonify({"ok": True})