# app/interfaces/http/app_usage_controller.py

from flask import Blueprint, current_app, jsonify, request

from app.application.use_cases.admin.get_app_usage_snapshot_use_case import (
    GetAppUsageSnapshotUseCase,
)
from app.application.use_cases.admin.record_integrated_app_usage_use_case import (
    RecordIntegratedAppUsageResult,
    RecordIntegratedAppUsageUseCase,
)
from app.domain.services.usage_tracking_consent_service import CALLER_APP_HEADER
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.authorization import require_permission
from app.interfaces.http.security.service_token import require_service_token
from app.interfaces.http.utils.errors import api_error

admin_app_usage_bp = Blueprint("admin_app_usage", __name__)


def _extract_caller_app_id(payload: dict) -> str | None:
    header_value = (request.headers.get(CALLER_APP_HEADER) or "").strip()
    if header_value:
        return header_value

    body_value = payload.get("callerAppId") or payload.get("caller_app_id")
    if body_value:
        return str(body_value).strip()

    return None


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


@admin_app_usage_bp.route("/integrations/app-usage/record", methods=["POST"])
@require_service_token()
def record_integrated_app_usage():
    """
    Registra uso backend-only com consentimento usage_tracking do usuário.
    Header: Authorization: Bearer <CORE_API_INTEGRATIONS_SERVICE_TOKEN>
    Header opcional: X-Delpi-Caller-App (id do plugin que originou a chamada)
    Body: { "appId": "api-delpi", "userId": "<uuid>", "routePath": "/optional" }
    """
    payload = request.get_json(silent=True) or {}
    app_id = payload.get("appId") or payload.get("app_id")
    user_id = payload.get("userId") or payload.get("user_id")
    route_path = payload.get("routePath") or payload.get("route_path")
    caller_app_id = _extract_caller_app_id(payload)

    if not app_id or not user_id:
        return api_error(
            "app_usage_record_invalid",
            "appId e userId são obrigatórios.",
            status=400,
        )

    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = RecordIntegratedAppUsageUseCase(uow).execute(
                app_id=str(app_id),
                user_id=str(user_id),
                route_path=str(route_path).strip() if route_path else None,
                caller_app_id=caller_app_id,
            )

            if result == RecordIntegratedAppUsageResult.SKIPPED_CONSENT:
                return jsonify({"recorded": False, "skipped": "usage_tracking_consent"}), 200

            if result == RecordIntegratedAppUsageResult.INVALID:
                return api_error(
                    "app_usage_record_rejected",
                    "App inexistente/inativa ou userId inválido.",
                    status=404,
                )

            uow.commit()

        return jsonify({"recorded": True}), 201
    except Exception as exc:
        return api_error("app_usage_record_failed", str(exc))
