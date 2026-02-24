# app/interfaces/http/admin/apps_controller.py

from flask import Blueprint, jsonify, request, g
from sqlalchemy import or_

from app.extensions.db import db
from app.infrastructure.db.models import App, AppManifest
from app.domain.services.audit_log_service import log_audit
from app.interfaces.http.utils.pagination import paginate_query
from app.domain.services.admin_event_service import emit_admin_event

from app.interfaces.http.utils.errors import (
    unauthorized,
    forbidden,
    not_found,
    bad_request,
    error_response,
)

apps_admin_bp = Blueprint(
    "apps_admin",
    __name__,
    url_prefix="/core-api/admin/apps"
)


# =========================================================
# AUTH
# =========================================================

def require_superadmin():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    if not getattr(user, "is_superadmin", False):
        return forbidden("Forbidden")

    return None


# =========================================================
# LIST
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
                App.base_path.ilike(f"%{q}%"),
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


# =========================================================
# UPDATE
# =========================================================

@apps_admin_bp.put("/<app_id>")
def update_app(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return not_found("Not found")

    data = request.get_json(force=True) or {}

    for field in ["active", "icon", "description"]:
        if field in data:
            setattr(app, field, data[field])

    db.session.commit()

    emit_admin_event("apps", "update", {"appId": str(app.id)})
    log_audit("apps.update", "app", app.id, {"payload": data})

    return jsonify({"ok": True})


# =========================================================
# DELETE
# =========================================================

@apps_admin_bp.delete("/<app_id>")
def delete_app(app_id: str):
    guard = require_superadmin()
    if guard:
        return guard

    app = App.query.get(app_id)
    if not app:
        return not_found("Not found")

    manifest = AppManifest.query.filter_by(app_id=app_id).first()
    if manifest:
        return error_response(
            code="app_delete_blocked_by_manifest",
            message="App registered via manifest cannot be deleted manually.",
            status=400,
        )

    db.session.delete(app)
    db.session.commit()

    emit_admin_event("apps", "delete", {"appId": app_id})
    log_audit("apps.delete", "app", app_id, {})

    return jsonify({"ok": True})


# =========================================================
# BULK ACTIONS
# =========================================================

def _parse_ids():
    ids = (request.get_json(force=True) or {}).get("ids", [])
    if not isinstance(ids, list) or not ids:
        return None, bad_request(
            "ids list required",
            code="validation_error",
            path="ids",
        )
    return ids, None


@apps_admin_bp.post("/bulk-delete")
def bulk_delete_apps():
    guard = require_superadmin()
    if guard:
        return guard

    ids, err = _parse_ids()
    if err:
        return err

    apps = App.query.filter(App.id.in_(ids)).all()

    for app in apps:
        if AppManifest.query.filter_by(app_id=app.id).first():
            return error_response(
                code="app_delete_blocked_by_manifest",
                message=f"App {app.id} registered via manifest cannot be deleted manually.",
                status=400,
                extra={"appId": str(app.id)},
            )

    for app in apps:
        db.session.delete(app)

    db.session.commit()

    emit_admin_event("apps", "bulk_delete", {"ids": ids})
    log_audit("apps.bulk_delete", "app", None, {"ids": ids})

    return jsonify({"ok": True, "deleted": len(apps)})


@apps_admin_bp.post("/bulk-activate")
def bulk_activate_apps():
    guard = require_superadmin()
    if guard:
        return guard

    ids, err = _parse_ids()
    if err:
        return err

    apps = App.query.filter(App.id.in_(ids)).all()
    for app in apps:
        app.active = True

    db.session.commit()
    emit_admin_event("apps", "bulk_update", {"ids": ids})

    return jsonify({"ok": True, "updated": len(apps)})


@apps_admin_bp.post("/bulk-deactivate")
def bulk_deactivate_apps():
    guard = require_superadmin()
    if guard:
        return guard

    ids, err = _parse_ids()
    if err:
        return err

    apps = App.query.filter(App.id.in_(ids)).all()
    for app in apps:
        app.active = False

    db.session.commit()
    emit_admin_event("apps", "bulk_update", {"ids": ids})

    return jsonify({"ok": True, "updated": len(apps)})