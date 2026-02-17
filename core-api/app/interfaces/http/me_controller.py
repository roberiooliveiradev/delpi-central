from flask import Blueprint, jsonify, g
from sqlalchemy.orm import joinedload

from app.domain.services.permission_resolver import resolve_user_permissions
from app.domain.services.app_resolver import resolve_user_apps
from app.infrastructure.db.models import AppRoute, Permission, App


me_bp = Blueprint("me", __name__)


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
        "is_superadmin": getattr(user, "is_superadmin", False),
        "roles": [{"id": str(r.id), "name": r.name} for r in user.roles],
        "groups": [{"id": str(gr.id), "name": gr.name} for gr in user.groups],
        "permissions": permissions
    })


@me_bp.route("/me/apps", methods=["GET"])
def me_apps():
    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    permissions = resolve_user_permissions(user)
    apps = resolve_user_apps(permissions)

    return jsonify(apps)


@me_bp.route("/me/routes", methods=["GET"])
def me_routes():
    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    permissions = set(resolve_user_permissions(user))

    # Carrega routes + app + permission numa única query
    routes = (
        AppRoute.query
        .options(
            joinedload(AppRoute.app),
            joinedload(AppRoute.permission),
        )
        .filter(AppRoute.active == True)
        .order_by(AppRoute.app_id.asc(), AppRoute.order.asc())
        .all()
    )

    allowed = []

    for route in routes:

        # Ignora app inativa
        if not route.app or not route.app.active:
            continue

        permission_code = None

        if route.permission:
            permission_code = route.permission.code

            if permission_code not in permissions:
                continue

        allowed.append({
            "app": route.app.id,
            "path": route.path,
            "permission": permission_code,
        })

    return jsonify(allowed)
