# app/interfaces/http/apps_admin_controller.py

from flask import Blueprint, jsonify, request, g
from sqlalchemy import or_
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
# Apps (READ / UPDATE / DELETE ONLY)
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
        default_sort="name",
    )


@apps_admin_bp.put("/<app_id>")
def update_app(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True) or {}

    # 🔒 Apenas campos administrativos podem ser alterados
    for field in ["active", "icon", "description"]:
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