# app/interfaces/http/notifications_controller.py

from flask import Blueprint, jsonify, request

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.use_cases.dispatch_notifications_use_case import (
    DispatchNotificationsUseCase,
    DispatchNotificationsValidationError,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.authorization import require_superadmin
from app.interfaces.http.security.service_token import require_service_token
from app.interfaces.http.utils.errors import api_error

admin_notifications_bp = Blueprint(
    "admin_notifications",
    __name__,
    url_prefix="/admin/notifications",
)

integrations_notifications_bp = Blueprint(
    "integrations_notifications",
    __name__,
    url_prefix="/integrations/notifications",
)


def _parse_dispatch_body(data: dict | None) -> DispatchNotificationsRequest:
    payload = data if isinstance(data, dict) else {}

    user_ids = payload.get("userIds") or payload.get("user_ids") or []
    emails = payload.get("emails") or []

    if not isinstance(user_ids, list):
        user_ids = []
    if not isinstance(emails, list):
        emails = []

    return DispatchNotificationsRequest(
        title=payload.get("title"),
        message=payload.get("message", ""),
        type=payload.get("type", "info"),
        broadcast=bool(payload.get("broadcast", False)),
        user_ids=[str(item) for item in user_ids if item],
        emails=[str(item) for item in emails if item],
        source_app=payload.get("sourceApp") or payload.get("source_app"),
    )


def _dispatch_notifications(request_dto: DispatchNotificationsRequest):
    with SqlAlchemyUnitOfWork() as uow:
        use_case = DispatchNotificationsUseCase(uow)
        result = use_case.execute(request_dto)

    return jsonify(
        {
            "createdCount": result.created_count,
            "notificationIds": result.notification_ids,
        }
    ), 201


@admin_notifications_bp.route("", methods=["POST"])
@require_superadmin()
def admin_dispatch_notifications():
    try:
        request_dto = _parse_dispatch_body(request.get_json(silent=True))
        return _dispatch_notifications(request_dto)
    except DispatchNotificationsValidationError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception as exc:
        return api_error("dispatch_failed", str(exc))


@integrations_notifications_bp.route("", methods=["POST"])
@require_service_token()
def integrations_dispatch_notifications():
    try:
        request_dto = _parse_dispatch_body(request.get_json(silent=True))
        return _dispatch_notifications(request_dto)
    except DispatchNotificationsValidationError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception as exc:
        return api_error("dispatch_failed", str(exc))
