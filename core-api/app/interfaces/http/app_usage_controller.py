# app/interfaces/http/app_usage_controller.py

from flask import Blueprint, current_app, jsonify

from app.application.use_cases.admin.get_app_usage_snapshot_use_case import (
    GetAppUsageSnapshotUseCase,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.authorization import require_permission
from app.interfaces.http.utils.errors import api_error

admin_app_usage_bp = Blueprint("admin_app_usage", __name__)


@admin_app_usage_bp.route("/admin/apps/usage", methods=["GET"])
@require_permission("rbac.manage")
def get_app_usage():
    try:
        history_days = int(current_app.config.get("APP_USAGE_HISTORY_DAYS", 30))

        with SqlAlchemyUnitOfWork() as uow:
            result = GetAppUsageSnapshotUseCase(uow).execute(history_days=history_days)

        return jsonify(result), 200
    except Exception as exc:
        return api_error("app_usage_failed", str(exc))
