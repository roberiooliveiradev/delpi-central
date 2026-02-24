# app/interfaces/http/admin/routes_controller.py

from flask import Blueprint, jsonify, request, g
from app.extensions.db import db
from app.infrastructure.db.models import AppRoute
from app.domain.services.audit_log_service import log_audit
from app.interfaces.http.utils.pagination import paginate_query


routes_admin_bp = Blueprint(
    "routes_admin",
    __name__,
    url_prefix="/core-api/admin/apps"
)


def require_superadmin():
    user = getattr(g, "current_user", None)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    if not getattr(user, "is_superadmin", False):
        return jsonify({"error": "Forbidden"}), 403
    return None


# =========================================================
# LIST
# =========================================================

@routes_admin_bp.get("/<app_id>/routes")
def list_routes(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    query = AppRoute.query.filter_by(app_id=app_id)

    return paginate_query(
        query,
        lambda r: {
            "id": str(r.id),
            "app_id": str(r.app_id),
            "path": r.path,
            "label": r.label,
            "icon": r.icon,
            "order": r.order,
            "active": r.active,
        },
        AppRoute,
        allowed_sort_fields=["path", "order", "active"],
        default_sort="order",
    )


# =========================================================
# UPDATE
# =========================================================

@routes_admin_bp.put("/routes/<route_id>")
def update_route(route_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    route = AppRoute.query.get(route_id)
    if not route:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}

    for field in ["label", "icon", "order", "active"]:
        if field in data:
            setattr(route, field, data[field])

    db.session.commit()
    log_audit("routes.update", "route", route_id, {"payload": data})

    return jsonify({"ok": True})


# =========================================================
# BULK
# =========================================================

@routes_admin_bp.post("/routes/bulk-activate")
def bulk_activate_routes():
    guard = require_superadmin()
    if guard:
        return guard

    ids = (request.get_json(force=True) or {}).get("ids", [])
    routes = AppRoute.query.filter(AppRoute.id.in_(ids)).all()

    for r in routes:
        r.active = True

    db.session.commit()
    return jsonify({"ok": True, "updated": len(routes)})


@routes_admin_bp.post("/routes/bulk-deactivate")
def bulk_deactivate_routes():
    guard = require_superadmin()
    if guard:
        return guard

    ids = (request.get_json(force=True) or {}).get("ids", [])
    routes = AppRoute.query.filter(AppRoute.id.in_(ids)).all()

    for r in routes:
        r.active = False

    db.session.commit()
    return jsonify({"ok": True, "updated": len(routes)})


@routes_admin_bp.post("/routes/bulk-delete")
def bulk_delete_routes():
    guard = require_superadmin()
    if guard:
        return guard

    ids = (request.get_json(force=True) or {}).get("ids", [])
    routes = AppRoute.query.filter(AppRoute.id.in_(ids)).all()

    for r in routes:
        db.session.delete(r)

    db.session.commit()
    return jsonify({"ok": True, "deleted": len(routes)})