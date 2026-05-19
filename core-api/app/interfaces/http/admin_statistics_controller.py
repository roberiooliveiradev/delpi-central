# app/interfaces/http/admin_statistics_controller.py

from flask import Blueprint, jsonify

from app.application.use_cases.admin.get_admin_statistics_use_case import (
    GetAdminStatisticsUseCase,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.authorization import require_permission
from app.interfaces.http.utils.errors import server_error

admin_statistics_bp = Blueprint("admin_statistics", __name__)


@admin_statistics_bp.route("/admin/statistics", methods=["GET"])
@require_permission("rbac.manage")
def get_admin_statistics():
    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = GetAdminStatisticsUseCase(uow).execute()

        return jsonify(result), 200
    except Exception as exc:
        return server_error(str(exc))
