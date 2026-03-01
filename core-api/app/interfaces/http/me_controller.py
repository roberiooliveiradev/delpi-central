# app/interfaces/http/me_controller.py

from flask import Blueprint, jsonify, g

from app.interfaces.http.utils.errors import unauthorized
from app.application.use_cases.get_me_use_case import GetMeUseCase
from app.application.use_cases.list_user_apps_use_case import ListUserAppsUseCase
from app.application.use_cases.list_user_routes_use_case import ListUserRoutesUseCase

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.domain.services.permission_resolver import PermissionResolver


me_bp = Blueprint("me", __name__)


def require_auth():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()
    return None


# ==========================================================
# GET /me
# ==========================================================
@me_bp.route("/me", methods=["GET"])
def get_me():
    guard = require_auth()
    if guard:
        return guard

    uc = GetMeUseCase()

    result = uc.execute(
        user=g.current_user,
        permissions=g.current_permissions,
    )

    return jsonify(result.__dict__), 200


# ==========================================================
# GET /me/apps
# ==========================================================
@me_bp.route("/me/apps", methods=["GET"])
def get_my_apps():
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()

    permission_resolver = PermissionResolver(uow.permission_queries)

    uc = ListUserAppsUseCase(
        uow.app_queries,
        permission_resolver,
    )

    result = uc.execute(
        user_id=g.current_user.id,  # UUID
        is_superadmin=getattr(g.current_user, "is_superadmin", False),
    )

    return jsonify(result), 200


# ==========================================================
# GET /me/routes
# ==========================================================
@me_bp.route("/me/routes", methods=["GET"])
def me_routes():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()

    permissions = g.current_permissions or []

    uow = SqlAlchemyUnitOfWork()

    uc = ListUserRoutesUseCase(
        route_queries=uow.route_queries
    )

    result = uc.execute(permissions)

    return jsonify(result), 200