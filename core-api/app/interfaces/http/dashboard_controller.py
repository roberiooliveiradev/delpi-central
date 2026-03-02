# app/interfaces/http/dashboard_controller.py

from flask import Blueprint, jsonify, g
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.application.use_cases.list_user_apps_use_case import ListUserAppsUseCase
from app.interfaces.http.utils.errors import unauthorized

dashboard_bp = Blueprint("dashboard", __name__)


def _get_user():
    user = getattr(g, "current_user", None)
    if not user:
        return None, unauthorized()
    return user, None


@dashboard_bp.route("/dashboard/apps", methods=["GET"])
def list_user_apps():
    user, error = _get_user()
    if error:
        return error

    with SqlAlchemyUnitOfWork() as uow:
        use_case = ListUserAppsUseCase(app_query=uow.app_queries)

        result = use_case.execute(
            permissions=user.permissions,
            is_superadmin=user.is_superadmin,
        )

    return jsonify(result), 200


@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():
    user, error = _get_user()
    if error:
        return error

    with SqlAlchemyUnitOfWork() as uow:
        use_case = ListUserAppsUseCase(app_query=uow.app_queries)

        result = use_case.execute(
            permissions=user.permissions,
            is_superadmin=user.is_superadmin,
        )

    return jsonify(result), 200