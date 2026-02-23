# app/interfaces/http/apps_admin_controller.py

from flask import Blueprint, jsonify, request, g
from app.extensions.db import db
from app.infrastructure.db.models import App, AppRoute, Permission
from app.domain.services.audit_log_service import log_audit
from app.interfaces.http.utils.pagination import paginate_query

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

@apps_admin_bp.route("", methods=["GET"])
def list_apps():
    guard = require_superadmin()
    if guard:
        return guard

    query = App.query.order_by(App.name.asc())

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
        }
    )


# =========================================================
# Routes
# =========================================================

@apps_admin_bp.route("/<app_id>/routes", methods=["GET"])
def list_routes(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "App not found"}), 404

    query = (
        AppRoute.query
        .filter_by(app_id=app_id)
        .order_by(AppRoute.path.asc())
    )

    def serializer(r):
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

    return paginate_query(query, serializer)