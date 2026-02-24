# app/interfaces/http/me_controller.py

from flask import Blueprint, jsonify, g, request
from sqlalchemy.orm import joinedload

from app.domain.services.favorite_app_service import FavoriteAppService
from app.domain.services.permission_resolver import resolve_user_permissions
from app.domain.services.app_resolver import resolve_user_apps
from app.infrastructure.db.models import AppRoute
from app.interfaces.http.utils.errors import (
    unauthorized,
    forbidden,
    bad_request,
)

me_bp = Blueprint("me", __name__)


@me_bp.route("/me", methods=["GET"])
def me():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    permissions = resolve_user_permissions(user)

    return jsonify({
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "is_superadmin": getattr(user, "is_superadmin", False),
        "roles": [{"id": str(r.id), "name": r.name} for r in user.roles],
        "groups": [{"id": str(gr.id), "name": gr.name} for gr in user.groups],
        "permissions": permissions,
    })


@me_bp.route("/me/apps", methods=["GET"])
def me_apps():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    permissions = resolve_user_permissions(user)
    apps = resolve_user_apps(permissions)

    return jsonify(apps)


@me_bp.route("/me/apps/favorites", methods=["GET"])
def me_favorite_app():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    favorites = FavoriteAppService.list_favorites(user)

    return jsonify([
        {
            "app_id": f.app_id,
            "order_index": f.order_index,
        }
        for f in favorites
    ])


@me_bp.route("/me/apps/favorites", methods=["POST"])
def me_add_favorite_app():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    data = request.get_json(silent=True) or {}
    app_id = data.get("app_id")

    if not app_id:
        # mantém seu padrão: code validation_error + path "app_id"
        return bad_request("app_id is required", code="validation_error", path="app_id")

    try:
        favorite = FavoriteAppService.add_favorite(user, app_id)

        return jsonify({
            "app_id": favorite.app_id,
            "order_index": favorite.order_index,
        }), 201

    except PermissionError as e:
        return forbidden(str(e) or "Forbidden")

    except ValueError as e:
        return bad_request(str(e) or "Invalid request", code="validation_error")


@me_bp.route("/me/apps/favorites", methods=["PUT"])
def me_order_favorite_app():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    data = request.get_json(silent=True)

    if not isinstance(data, list):
        return bad_request("Invalid payload format", code="validation_error")

    try:
        FavoriteAppService.reorder_favorites(user, data)
        return jsonify({"ok": True})

    except ValueError as e:
        return bad_request(str(e) or "Invalid request", code="validation_error")


@me_bp.route("/me/apps/favorites", methods=["DELETE"])
def me_delete_favorite_app():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    data = request.get_json(silent=True) or {}
    app_id = data.get("app_id")

    if not app_id:
        return bad_request("app_id is required", code="validation_error", path="app_id")

    try:
        FavoriteAppService.remove_favorite(user, app_id)
        return jsonify({"ok": True})

    except ValueError as e:
        return bad_request(str(e) or "Invalid request", code="validation_error")


@me_bp.route("/me/routes", methods=["GET"])
def me_routes():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    permissions = set(resolve_user_permissions(user))

    routes = (
        AppRoute.query
        .options(
            joinedload(AppRoute.app),
            joinedload(AppRoute.permission),
        )
        .filter(
            AppRoute.active == True,
            AppRoute.show_in_menu == True
        )
        .order_by(AppRoute.app_id.asc(), AppRoute.order.asc())
        .all()
    )

    allowed: list[dict] = []

    for route in routes:
        # ignora app inativa
        if not route.app or not route.app.active:
            continue

        permission_code = None
        if route.permission:
            permission_code = route.permission.code
            if permission_code not in permissions:
                continue

        allowed.append({
            "app": route.app.id,
            "app_name": route.app.name,
            "app_icon": route.app.icon,
            "path": route.path,
            "permission": permission_code,
            "icon": route.icon,
            "label": route.label,
        })

    return jsonify(allowed)