# app/interfaces/http/me_controller.py


from flask import Blueprint, jsonify, g, request
from sqlalchemy.orm import joinedload
from app.domain.services.favorite_app_service import FavoriteAppService
from app.infrastructure.db.models import UserFavoriteApp

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


@me_bp.route("/me/apps/favorites", methods=["GET"])
def me_favorite_app():
    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    favorites = FavoriteAppService.list_favorites(user)

    result = [
        {
            "app_id": f.app_id,
            "order_index": f.order_index
        }
        for f in favorites
    ]

    return jsonify(result)



@me_bp.route("/me/apps/favorites", methods=["POST"])
def me_add_favorite_app():
    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    app_id = data.get("app_id")

    if not app_id:
        return jsonify({"error": "app_id is required"}), 400

    try:
        favorite = FavoriteAppService.add_favorite(user, app_id)

        return jsonify({
            "app_id": favorite.app_id,
            "order_index": favorite.order_index
        }), 201

    except PermissionError as e:
        return jsonify({"error": str(e)}), 403

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@me_bp.route("/me/apps/favorites", methods=["PUT"])
def me_order_favorite_app():
    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({"error": "Invalid payload format"}), 400

    try:
        FavoriteAppService.reorder_favorites(user, data)
        return jsonify({"message": "Favorites reordered successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@me_bp.route("/me/apps/favorites", methods=["DELETE"])
def me_delete_favorite_app():
    user = getattr(g, "current_user", None)

    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    app_id = data.get("app_id")

    if not app_id:
        return jsonify({"error": "app_id is required"}), 400

    try:
        FavoriteAppService.remove_favorite(user, app_id)
        return jsonify({"message": "Favorite removed successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400




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
