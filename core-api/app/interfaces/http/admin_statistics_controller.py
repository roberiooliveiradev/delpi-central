# app/interfaces/http/admin_statistics_controller.py

import logging

from flask import Blueprint, jsonify, request

from app.application.use_cases.admin.get_admin_statistics_use_case import (
    GetAdminStatisticsUseCase,
)
from app.application.use_cases.admin.get_engagement_statistics_use_case import (
    ALLOWED_PERIOD_DAYS,
    GetEngagementStatisticsUseCase,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.authorization import require_permission
from app.interfaces.http.utils.errors import bad_request, server_error

logger = logging.getLogger(__name__)

admin_statistics_bp = Blueprint("admin_statistics", __name__)


@admin_statistics_bp.route("/admin/statistics", methods=["GET"])
@require_permission("rbac.manage")
def get_admin_statistics():
    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = GetAdminStatisticsUseCase(uow).execute()

        return jsonify(result), 200
    except Exception as exc:
        logger.exception("get_admin_statistics_failed")
        return server_error()


@admin_statistics_bp.route("/admin/statistics/engagement", methods=["GET"])
@require_permission("rbac.manage")
def get_engagement_statistics():
    try:
        raw_period = request.args.get("periodDays") or request.args.get("period_days") or "30"
        try:
            period_days = int(raw_period)
        except (TypeError, ValueError):
            return bad_request("Parâmetro periodDays inválido.")

        if period_days not in ALLOWED_PERIOD_DAYS:
            return bad_request("periodDays deve ser 7, 30 ou 90.")

        with SqlAlchemyUnitOfWork() as uow:
            result = GetEngagementStatisticsUseCase(uow).execute(
                period_days=period_days,
            )

        return jsonify(result), 200
    except ValueError as exc:
        return bad_request(str(exc))
    except Exception:
        logger.exception("get_engagement_statistics_failed")
        return server_error()
