# app/interfaces/http/dashboard_controller.py

from flask import Blueprint, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.domain.services.permission_resolver import PermissionResolver
from app.application.use_cases.list_user_apps_use_case import ListUserAppsUseCase

from app.interfaces.http.utils.errors import unauthorized


dashboard_bp = Blueprint("dashboard", __name__)


def require_auth():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()
    return None


# ---------------------------------------------------------
# GET /dashboard/apps
# ---------------------------------------------------------

@dashboard_bp.route("/dashboard/apps", methods=["GET"])
def list_user_apps():
    guard = require_auth()
    if guard:
        return guard

    with SqlAlchemyUnitOfWork() as uow:
        permission_resolver = PermissionResolver(
            permission_query=uow.permission_queries
        )

        use_case = ListUserAppsUseCase(
            app_query=uow.app_queries,
            permission_resolver=permission_resolver,
        )

        result = use_case.execute(
            user_id=g.current_user.id,
            is_superadmin=getattr(g.current_user, "is_superadmin", False),
        )

    return jsonify(result), 200

# ---------------------------------------------------------
# GET /dashboard  (compatibilidade com frontend)
# ---------------------------------------------------------

@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():
    guard = require_auth()
    if guard:
        return guard

    with SqlAlchemyUnitOfWork() as uow:
        permission_resolver = PermissionResolver(
            permission_query=uow.permission_queries
        )

        use_case = ListUserAppsUseCase(
            app_query=uow.app_queries,
            permission_resolver=permission_resolver,
        )

        result = use_case.execute(
            user_id=g.current_user.id,
            is_superadmin=getattr(g.current_user, "is_superadmin", False),
        )

    return jsonify(result), 200