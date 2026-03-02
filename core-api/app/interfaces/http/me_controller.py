from flask import Blueprint, jsonify, g
from app.interfaces.http.utils.errors import unauthorized
from app.application.use_cases.list_user_apps_use_case import ListUserAppsUseCase
from app.application.use_cases.list_user_routes_use_case import ListUserRoutesUseCase
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork


me_bp = Blueprint("me", __name__)


# ==========================================================
# GET /me
# ==========================================================
@me_bp.route("/me", methods=["GET"])
def get_me():
    user = getattr(g, "current_user", None)

    if not user:
        return unauthorized()

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "roles": getattr(user, "roles", []),
        "groups": getattr(user, "groups", []),
        "permissions": getattr(user, "permissions", []),
        "is_superadmin": getattr(user, "is_superadmin", False),
    }), 200


# ==========================================================
# GET /me/apps
# ==========================================================
@me_bp.route("/me/apps", methods=["GET"])
def get_my_apps():
    user = getattr(g, "current_user", None)

    if not user:
        return unauthorized()

    with SqlAlchemyUnitOfWork() as uow:
        uc = ListUserAppsUseCase(
            uow.app_queries
        )

        result = uc.execute(
            permissions=user.permissions,
            is_superadmin=user.is_superadmin,
        )

    return jsonify(result), 200


# ==========================================================
# GET /me/routes
# ==========================================================
@me_bp.route("/me/routes", methods=["GET"])
def get_my_routes():
    user = getattr(g, "current_user", None)

    if not user:
        return unauthorized()

    with SqlAlchemyUnitOfWork() as uow:
        uc = ListUserRoutesUseCase(
            uow.route_queries
        )

        result = uc.execute(
            permissions=user.permissions,
            is_superadmin=user.is_superadmin,
        )

    return jsonify(result), 200