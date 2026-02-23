# app/interfaces/http/apps_admin_controller.py

from flask import Blueprint, jsonify, request, g
from sqlalchemy import or_
from app.extensions.db import db
from app.infrastructure.db.models import App, AppRoute, Permission
from app.domain.services.audit_log_service import log_audit
from app.interfaces.http.utils.pagination import paginate_query

# ✅ IMPORTANTE: blueprint precisa existir no topo do módulo
apps_admin_bp = Blueprint(
    "apps_admin",
    __name__,
    url_prefix="/core-api/admin/apps"
)

# =========================================================
# Auth
# =========================================================

def require_superadmin():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if not getattr(user, "is_superadmin", False):
        return jsonify({"error": "Forbidden"}), 403
    return None


# =========================================================
# Apps
# =========================================================

@apps_admin_bp.get("")
def list_apps():
    guard = require_superadmin()
    if guard:
        return guard

    q = (request.args.get("q") or "").strip().lower()

    query = App.query
    if q:
        query = query.filter(
            or_(
                App.name.ilike(f"%{q}%"),
                App.base_path.ilike(f"%{q}%")
            )
        )

    return paginate_query(
        query,
        lambda a: {
            "id": str(a.id),
            "name": a.name,
            "description": a.description,
            "base_path": a.base_path,
            "icon": a.icon,
            "type": a.type,
            "version": a.version,
            "active": a.active,
        },
        App,
        allowed_sort_fields=["name", "version", "active", "type", "base_path"],
        allowed_filter_fields=["active", "type"],
        default_sort="name",
        default_direction="asc",
    )


@apps_admin_bp.post("")
def create_app():
    guard = require_superadmin()
    if guard:
        return guard

    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    app = App(
        name=name,
        description=data.get("description"),
        base_path=data.get("base_path"),
        icon=data.get("icon"),
        type=data.get("type"),
        version=data.get("version"),
        active=bool(data.get("active", True)),
    )
    db.session.add(app)
    db.session.commit()

    log_audit("apps.create", "app", app.id, {"payload": data})
    return jsonify({"ok": True, "id": str(app.id)}), 201


@apps_admin_bp.put("/<app_id>")
def update_app(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}

    for field in ["name", "description", "base_path", "icon", "type", "version", "active"]:
        if field in data:
            setattr(app, field, data[field])

    db.session.commit()
    log_audit("apps.update", "app", app.id, {"payload": data})

    return jsonify({"ok": True})


@apps_admin_bp.delete("/<app_id>")
def delete_app(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(app)
    db.session.commit()

    log_audit("apps.delete", "app", app_id, {})
    return jsonify({"ok": True})


@apps_admin_bp.post("/bulk-activate")
def bulk_activate_apps():
    guard = require_superadmin()
    if guard:
        return guard

    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "ids list required"}), 400

    apps = App.query.filter(App.id.in_(ids)).all()
    for app in apps:
        app.active = True

    db.session.commit()
    log_audit("apps.bulk_activate", "app", None, {"ids": ids})
    return jsonify({"ok": True, "updated": len(apps)})


@apps_admin_bp.post("/bulk-deactivate")
def bulk_deactivate_apps():
    guard = require_superadmin()
    if guard:
        return guard

    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "ids list required"}), 400

    apps = App.query.filter(App.id.in_(ids)).all()
    for app in apps:
        app.active = False

    db.session.commit()
    log_audit("apps.bulk_deactivate", "app", None, {"ids": ids})
    return jsonify({"ok": True, "updated": len(apps)})


@apps_admin_bp.post("/bulk-delete")
def bulk_delete_apps():
    guard = require_superadmin()
    if guard:
        return guard

    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "ids list required"}), 400

    apps = App.query.filter(App.id.in_(ids)).all()
    for app in apps:
        db.session.delete(app)

    db.session.commit()
    log_audit("apps.bulk_delete", "app", None, {"ids": ids})
    return jsonify({"ok": True, "deleted": len(apps)})


# =========================================================
# Routes
# =========================================================

@apps_admin_bp.get("/<app_id>/routes")
def list_routes(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "App not found"}), 404

    q = (request.args.get("q") or "").strip().lower()

    query = AppRoute.query.filter_by(app_id=app_id)
    if q:
        query = query.filter(
            or_(
                AppRoute.path.ilike(f"%{q}%"),
                AppRoute.label.ilike(f"%{q}%")
            )
        )

    def serializer(r: AppRoute):
        permission_code = None
        if getattr(r, "permission_id", None):
            p = Permission.query.get(r.permission_id)
            if p:
                permission_code = p.code

        return {
            "id": str(r.id),
            "app_id": str(r.app_id),
            "path": r.path,
            "label": getattr(r, "label", None),
            "icon": getattr(r, "icon", None),
            "order": getattr(r, "order", None),
            "show_in_menu": getattr(r, "show_in_menu", None),
            "active": getattr(r, "active", True),
            "permission_code": permission_code,
            "permission_id": str(r.permission_id) if getattr(r, "permission_id", None) else None,
        }

    return paginate_query(
        query,
        serializer,
        AppRoute,
        allowed_sort_fields=["path", "label", "active", "order", "show_in_menu"],
        allowed_filter_fields=["active", "show_in_menu"],
        default_sort="path",
        default_direction="asc",
    )


@apps_admin_bp.post("/<app_id>/routes")
def create_route(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "App not found"}), 404

    data = request.get_json(force=True) or {}
    path = (data.get("path") or "").strip()
    if not path:
        return jsonify({"error": "path is required"}), 400

    route = AppRoute(
        app_id=app_id,
        path=path,
        label=data.get("label"),
        icon=data.get("icon"),
        order=data.get("order"),
        show_in_menu=bool(data.get("show_in_menu", True)),
        active=bool(data.get("active", True)),
        permission_id=data.get("permission_id"),
    )
    db.session.add(route)
    db.session.commit()

    log_audit("routes.create", "route", route.id, {"payload": data})
    return jsonify({"ok": True, "id": str(route.id)}), 201


@apps_admin_bp.put("/routes/<route_id>")
def update_route(route_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    route = AppRoute.query.get(route_id)
    if not route:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}

    for field in ["path", "label", "icon", "order", "show_in_menu", "active", "permission_id"]:
        if field in data:
            setattr(route, field, data[field])

    db.session.commit()
    log_audit("routes.update", "route", route_id, {"payload": data})
    return jsonify({"ok": True})


@apps_admin_bp.delete("/routes/<route_id>")
def delete_route(route_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    route = AppRoute.query.get(route_id)
    if not route:
        return jsonify({"error": "Not found"}), 404

    db.session.delete(route)
    db.session.commit()

    log_audit("routes.delete", "route", route_id, {})
    return jsonify({"ok": True})


@apps_admin_bp.post("/routes/bulk-delete")
def bulk_delete_routes():
    guard = require_superadmin()
    if guard:
        return guard

    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "ids list required"}), 400

    routes = AppRoute.query.filter(AppRoute.id.in_(ids)).all()
    for r in routes:
        db.session.delete(r)

    db.session.commit()
    log_audit("routes.bulk_delete", "route", None, {"ids": ids})
    return jsonify({"ok": True, "deleted": len(routes)})


@apps_admin_bp.post("/routes/bulk-activate")
def bulk_activate_routes():
    guard = require_superadmin()
    if guard:
        return guard

    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "ids list required"}), 400

    routes = AppRoute.query.filter(AppRoute.id.in_(ids)).all()
    for r in routes:
        r.active = True

    db.session.commit()
    log_audit("routes.bulk_activate", "route", None, {"ids": ids})
    return jsonify({"ok": True, "updated": len(routes)})


@apps_admin_bp.post("/routes/bulk-deactivate")
def bulk_deactivate_routes():
    guard = require_superadmin()
    if guard:
        return guard

    data = request.get_json(force=True) or {}
    ids = data.get("ids", [])
    if not isinstance(ids, list) or not ids:
        return jsonify({"error": "ids list required"}), 400

    routes = AppRoute.query.filter(AppRoute.id.in_(ids)).all()
    for r in routes:
        r.active = False

    db.session.commit()
    log_audit("routes.bulk_deactivate", "route", None, {"ids": ids})
    return jsonify({"ok": True, "updated": len(routes)})