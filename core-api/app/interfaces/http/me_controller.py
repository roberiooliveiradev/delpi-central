# app/interfaces/http/me_controller.py

from flask import Blueprint, jsonify, g
from app.domain.services.permission_resolver import resolve_user_permissions
from app.domain.services.app_resolver import resolve_user_apps

me_bp = Blueprint("me", __name__, url_prefix="/core-api")

@me_bp.route("/me", methods=["GET"])
def me():

    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    permissions = resolve_user_permissions(user)

    return jsonify({
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "roles": [r.name for r in user.roles],
        "groups": [g.name for g in user.groups],
        "permissions": permissions
    })

@me_bp.route("/me/apps", methods=["GET"])
def me_apps():

    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    from app.domain.services.permission_resolver import resolve_user_permissions

    permissions = resolve_user_permissions(user)

    apps = resolve_user_apps(permissions)

    return jsonify(apps)

@me_bp.route("/me/routes", methods=["GET"])
def me_routes():

    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    from app.domain.services.permission_resolver import resolve_user_permissions
    from app.infrastructure.db.models import AppRoute, Permission, App

    permissions = resolve_user_permissions(user)

    routes = AppRoute.query.filter_by(active=True).all()

    allowed = []

    for route in routes:

        permission_code = None

        if route.permission_id:
            permission = Permission.query.get(route.permission_id)

            if not permission:
                continue

            permission_code = permission.code

            if permission_code not in permissions:
                continue

        app = App.query.get(route.app_id)

        allowed.append({
            "app": app.id if app else None,
            "path": route.path,
            "permission": permission_code
        })

    return jsonify(allowed)
