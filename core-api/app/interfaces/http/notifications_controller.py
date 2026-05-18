# app/interfaces/http/notifications_controller.py

from datetime import datetime

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


def _parse_action(payload: dict) -> tuple[str | None, str | None, str | None]:
    action = payload.get("action")
    if not action:
        action_type = payload.get("actionType") or payload.get("action_type")
        return (
            action_type,
            payload.get("actionLabel") or payload.get("action_label"),
            payload.get("actionTarget") or payload.get("action_target"),
        )

    if not isinstance(action, dict):
        return None, None, None

    return (
        action.get("type"),
        action.get("label"),
        action.get("target"),
    )


def _parse_expires_at(value) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    try:
        normalized = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).replace(tzinfo=None)
    except ValueError as exc:
        raise DispatchNotificationsValidationError("expiresAt must be ISO-8601 datetime") from exc


def _parse_dispatch_body(data: dict | None) -> DispatchNotificationsRequest:
    payload = data if isinstance(data, dict) else {}

    user_ids = payload.get("userIds") or payload.get("user_ids") or []
    emails = payload.get("emails") or []

    if not isinstance(user_ids, list):
        user_ids = []
    if not isinstance(emails, list):
        emails = []

    action_type, action_label, action_target = _parse_action(payload)

    metadata = payload.get("metadata")
    if metadata is not None and not isinstance(metadata, dict):
        raise DispatchNotificationsValidationError("metadata must be an object")

    presentation = (payload.get("presentation") or "text").strip().lower()
    if presentation == "template":
        template_id = payload.get("templateId") or payload.get("template_id")
        template_vars = payload.get("templateVars") or payload.get("template_vars") or {}
        metadata = {
            **(metadata or {}),
            "templateId": template_id,
            "vars": template_vars if isinstance(template_vars, dict) else {},
        }

    return DispatchNotificationsRequest(
        title=payload.get("title"),
        message=payload.get("message", ""),
        type=payload.get("type", "info"),
        category=payload.get("category", "system"),
        presentation=presentation,
        html_content=payload.get("htmlContent") or payload.get("html_content"),
        action_type=action_type,
        action_label=action_label,
        action_target=action_target,
        icon=payload.get("icon"),
        metadata=metadata,
        expires_at=_parse_expires_at(payload.get("expiresAt") or payload.get("expires_at")),
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
