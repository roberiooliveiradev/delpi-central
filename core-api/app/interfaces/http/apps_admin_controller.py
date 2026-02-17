# app/interfaces/http/apps_admin_controller.py

from flask import Blueprint, jsonify, request, g
from datetime import datetime

from app.extensions.db import db
from app.infrastructure.db.models import App, AppRoute, Permission


apps_admin_bp = Blueprint("apps_admin", __name__, url_prefix="/core-api/admin/apps")

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


# =========================================================
# APPS
# =========================================================

@apps_admin_bp.route("", methods=["GET"])
def list_apps():
    guard = require_superadmin()
    if guard:
        return guard

    rows = App.query.order_by(App.name.asc()).all()

    return jsonify([
        {
            "id": str(a.id),
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



@apps_admin_bp.route("", methods=["POST"])
def create_app():
    guard = require_superadmin()
    if guard:
        return guard

    data = request.get_json(silent=True) or {}

    app_id = data.get("id")
    name = data.get("name")
    base_path = data.get("base_path")
    icon = data.get("icon")
    version = data.get("version", "1.0.0")
    active = data.get("active", True)
    type_value = data.get("type")

    # 🔐 VALIDAÇÕES OBRIGATÓRIAS
    if not app_id or not name or not base_path or not type_value:
        return jsonify({
            "error": "Fields required: id, name, base_path, type"
        }), 400

    if App.query.get(app_id):
        return jsonify({"error": "App already exists"}), 409

    app = App(
        id=app_id,
        name=name,
        description=data.get("description"),
        base_path=base_path,
        icon=icon,
        type=type_value,   # ✅ AGORA O TYPE É SETADO
        version=version,
        active=active,
    )

    db.session.add(app)
    db.session.commit()

    return jsonify({"ok": True, "id": str(app.id)}), 201


@apps_admin_bp.route("/<app_id>", methods=["PUT"])
def update_app(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True) or {}

    if "name" in data:
        app.name = data["name"]
    if "description" in data:
        app.description = data["description"]
    if "version" in data:
        app.version = data["version"]
    if "base_path" in data:
        app.base_path = data["base_path"]
    if "icon" in data:
        app.icon = data["icon"]
    if "active" in data:
        app.active = bool(data["active"])
    if "type" in data:
        app.type = data["type"]

    db.session.commit()
    return jsonify({"ok": True})

@apps_admin_bp.route("/<app_id>/activate", methods=["POST"])
def activate_app(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "Not found"}), 404

    if hasattr(app, "active"):
        setattr(app, "active", True)
    db.session.commit()
    return jsonify({"ok": True})


@apps_admin_bp.route("/<app_id>/deactivate", methods=["POST"])
def deactivate_app(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "Not found"}), 404

    if hasattr(app, "active"):
        setattr(app, "active", False)
    db.session.commit()
    return jsonify({"ok": True})


# =========================================================
# ROUTES (NESTED)
# =========================================================

@apps_admin_bp.route("/<app_id>/routes", methods=["GET"])
def list_routes(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "App not found"}), 404

    routes = AppRoute.query.filter_by(app_id=app_id).order_by(AppRoute.path.asc()).all()

    def perm_code(route: AppRoute):
        if getattr(route, "permission_id", None):
            p = Permission.query.get(route.permission_id)
            return p.code if p else None
        return None

    return jsonify([
        {
            "id": str(r.id),
            "app_id": str(r.app_id),
            "path": r.path,
            "label": getattr(r, "label", None),
            "icon": getattr(r, "icon", None),
            "order": getattr(r, "order", None),
            "show_in_menu": getattr(r, "show_in_menu", None),
            "active": getattr(r, "active", True),
            "permission_code": perm_code(r),
            "permission_id": str(r.permission_id) if getattr(r, "permission_id", None) else None,
        }
        for r in routes
    ])


@apps_admin_bp.route("/<app_id>/routes", methods=["POST"])
def create_route(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "App not found"}), 404

    data = request.get_json(silent=True) or {}

    path = data.get("path")
    if not path:
        return jsonify({"error": "Field required: path"}), 400

    # 🚨 VALIDAÇÃO DE DUPLICIDADE
    existing = AppRoute.query.filter_by(app_id=app_id, path=path).first()
    if existing:
        return jsonify({"error": "Route already exists for this app"}), 409

    permission_id = data.get("permission_id")
    permission_code = data.get("permission_code")

    if permission_code and not permission_id:
        p = Permission.query.filter_by(code=permission_code).first()
        if not p:
            return jsonify({"error": f"Permission not found: {permission_code}"}), 400
        permission_id = str(p.id)

    route = AppRoute(
        app_id=app_id,
        path=path,
        permission_id=permission_id
    )

    if hasattr(route, "label") and "label" in data:
        route.label = data["label"]

    if hasattr(route, "icon") and "icon" in data:
        route.icon = data["icon"]

    if hasattr(route, "order") and "order" in data:
        route.order = data["order"]

    if hasattr(route, "show_in_menu") and "show_in_menu" in data:
        route.show_in_menu = bool(data["show_in_menu"])

    if hasattr(route, "active"):
        route.active = bool(data.get("active", True))

    db.session.add(route)
    db.session.commit()

    return jsonify({"ok": True, "id": str(route.id)}), 201


@apps_admin_bp.route("/routes/<route_id>", methods=["PUT"])
def update_route(route_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    route = AppRoute.query.get(route_id)
    if not route:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True) or {}

    if "path" in data:
        route.path = data["path"]

    if hasattr(route, "label") and "label" in data:
        route.label = data["label"]
    if hasattr(route, "icon") and "icon" in data:
        route.icon = data["icon"]
    if hasattr(route, "order") and "order" in data:
        route.order = data["order"]
    if hasattr(route, "show_in_menu") and "show_in_menu" in data:
        route.show_in_menu = bool(data["show_in_menu"])
    if hasattr(route, "active") and "active" in data:
        route.active = bool(data["active"])

    # permission update
    if hasattr(route, "permission_id"):
        if "permission_id" in data:
            route.permission_id = data["permission_id"]
        if "permission_code" in data:
            code = data["permission_code"]
            if code is None or code == "":
                route.permission_id = None
            else:
                p = Permission.query.filter_by(code=code).first()
                if not p:
                    return jsonify({"error": f"Permission not found: {code}"}), 400
                route.permission_id = str(p.id)

    db.session.commit()
    return jsonify({"ok": True})


@apps_admin_bp.route("/routes/<route_id>/activate", methods=["POST"])
def activate_route(route_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    route = AppRoute.query.get(route_id)
    if not route:
        return jsonify({"error": "Not found"}), 404

    if hasattr(route, "active"):
        route.active = True
    db.session.commit()
    return jsonify({"ok": True})


@apps_admin_bp.route("/routes/<route_id>/deactivate", methods=["POST"])
def deactivate_route(route_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    route = AppRoute.query.get(route_id)
    if not route:
        return jsonify({"error": "Not found"}), 404

    if hasattr(route, "active"):
        route.active = False
    db.session.commit()
    return jsonify({"ok": True})
