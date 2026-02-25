# app/interfaces/http/dashboard_controller.py

from flask import Blueprint, jsonify, g

from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork

from app.application.use_cases.list_user_apps_use_case import ListUserAppsUseCase

from app.interfaces.http.utils.errors import unauthorized


dashboard_bp = Blueprint("dashboard", __name__)


def require_auth():
    user = getattr(g, "current_user", None)
    if not user:
        return unauthorized()
    return None


# ---------------------------------------------------------
# Dashboard - apps do usuário
# ---------------------------------------------------------

@dashboard_bp.route("/dashboard/apps", methods=["GET"])
def list_user_apps():
    guard = require_auth()
    if guard:
        return guard

    uow = SqlAlchemyUnitOfWork()
    use_case = ListUserAppsUseCase(uow)

    result = use_case.execute(user_id=str(g.current_user.id))

    return jsonify(result), 200