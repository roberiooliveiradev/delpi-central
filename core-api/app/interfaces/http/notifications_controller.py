# app/interfaces/http/notifications_controller.py

from datetime import datetime
from uuid import UUID

from flask import Blueprint, g, jsonify, request

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.application.use_cases.create_notification_dispatch_use_case import (
    CreateNotificationDispatchUseCase,
)
from app.application.use_cases.dispatch_notifications_use_case import (
    DispatchNotificationsValidationError,
)
from app.application.use_cases.list_notification_dispatches_use_case import (
    ListNotificationDispatchesUseCase,
)
from app.application.use_cases.update_scheduled_notification_dispatch_use_case import (
    UpdateScheduledNotificationDispatchUseCase,
)
from app.application.use_cases.process_pending_notification_dispatches_use_case import (
    ProcessPendingNotificationDispatchesUseCase,
)
from app.application.use_cases.process_birthday_notifications_use_case import (
    ProcessBirthdayNotificationsUseCase,
)
from app.application.use_cases.manage_notification_templates_use_case import (
    CreateNotificationCustomTemplateUseCase,
    DeleteNotificationCustomTemplateUseCase,
    ListNotificationTemplatesUseCase,
    ManageNotificationTemplatesValidationError,
    build_template_registry,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork
from app.interfaces.http.security.authorization import require_superadmin
from app.extensions.integration_rate_limit import integration_rate_limit
from app.interfaces.http.security.service_token import require_service_token
from app.interfaces.http.serializers.notification_dispatch_serializer import (
    serialize_dispatch_result,
    serialize_notification_dispatch,
)
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


def _parse_scheduled_at(value) -> datetime | None:
    if not value:
        return None

    if isinstance(value, datetime):
        return value.replace(tzinfo=None)

    try:
        normalized = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(normalized).replace(tzinfo=None)
    except ValueError as exc:
        raise DispatchNotificationsValidationError(
            "scheduledAt must be ISO-8601 datetime"
        ) from exc


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
    role_ids = payload.get("roleIds") or payload.get("role_ids") or []
    group_ids = payload.get("groupIds") or payload.get("group_ids") or []

    if not isinstance(user_ids, list):
        user_ids = []
    if not isinstance(emails, list):
        emails = []
    if not isinstance(role_ids, list):
        role_ids = []
    if not isinstance(group_ids, list):
        group_ids = []

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
        role_ids=[str(item) for item in role_ids if item],
        group_ids=[str(item) for item in group_ids if item],
        source_app=payload.get("sourceApp") or payload.get("source_app"),
    )


def _dispatch_notifications(request_dto: DispatchNotificationsRequest, scheduled_at=None):
    registry = build_template_registry()
    actor_id = str(g.current_user.id) if getattr(g, "current_user", None) else None

    with SqlAlchemyUnitOfWork() as uow:
        result = CreateNotificationDispatchUseCase(
            uow,
            template_registry=registry,
        ).execute(
            request_dto,
            created_by_user_id=actor_id,
            scheduled_at=scheduled_at,
        )

    payload = serialize_dispatch_result(result)
    payload["createdCount"] = result.created_count
    payload["notificationIds"] = result.notification_ids

    status_code = 202 if result.status == "pending" else 201
    return jsonify(payload), status_code


def _parse_scheduled_at_from_body(payload: dict) -> datetime | None:
    return _parse_scheduled_at(payload.get("scheduledAt") or payload.get("scheduled_at"))


@admin_notifications_bp.route("", methods=["POST"])
@require_superadmin()
def admin_dispatch_notifications():
    try:
        body = request.get_json(silent=True) or {}
        request_dto = _parse_dispatch_body(body)
        scheduled_at = _parse_scheduled_at_from_body(body)
        return _dispatch_notifications(request_dto, scheduled_at=scheduled_at)
    except DispatchNotificationsValidationError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception as exc:
        return api_error("dispatch_failed", str(exc))


@admin_notifications_bp.route("/dispatches", methods=["GET"])
@require_superadmin()
def list_notification_dispatches():
    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return api_error("invalid_pagination", "limit and offset must be integers", status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = ListNotificationDispatchesUseCase(uow).execute(limit=limit, offset=offset)

        return (
            jsonify(
                {
                    "items": [
                        serialize_notification_dispatch(item) for item in result.items
                    ],
                    "total": result.total,
                    "limit": result.limit,
                    "offset": result.offset,
                }
            ),
            200,
        )
    except Exception as exc:
        return api_error("list_dispatches_failed", str(exc))


@admin_notifications_bp.route("/dispatches/<dispatch_id>", methods=["GET"])
@require_superadmin()
def get_notification_dispatch(dispatch_id: str):
    try:
        dispatch_uuid = UUID(dispatch_id)
    except ValueError:
        return api_error("invalid_id", "Invalid dispatch id", status=400)

    try:
        with SqlAlchemyUnitOfWork() as uow:
            dispatch = uow.notification_dispatches.get(dispatch_uuid)

        if not dispatch:
            return api_error("not_found", "Dispatch not found", status=404)

        return jsonify(serialize_notification_dispatch(dispatch, include_payload=True)), 200
    except Exception as exc:
        return api_error("get_dispatch_failed", str(exc))


@admin_notifications_bp.route("/dispatches/<dispatch_id>", methods=["PUT"])
@require_superadmin()
def update_scheduled_notification_dispatch(dispatch_id: str):
    try:
        dispatch_uuid = UUID(dispatch_id)
    except ValueError:
        return api_error("invalid_id", "Invalid dispatch id", status=400)

    try:
        body = request.get_json(silent=True) or {}
        request_dto = _parse_dispatch_body(body)
        scheduled_at = _parse_scheduled_at_from_body(body)
        if not scheduled_at:
            return api_error(
                "validation_error",
                "scheduledAt is required for scheduled dispatches",
                status=400,
            )

        with SqlAlchemyUnitOfWork() as uow:
            updated = UpdateScheduledNotificationDispatchUseCase(uow).execute(
                dispatch_uuid,
                request_dto,
                scheduled_at=scheduled_at,
            )

        return (
            jsonify(
                {
                    **serialize_notification_dispatch(updated),
                    "scheduledAt": updated.scheduled_at.isoformat() + "Z"
                    if updated.scheduled_at
                    else None,
                }
            ),
            200,
        )
    except DispatchNotificationsValidationError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception as exc:
        return api_error("update_dispatch_failed", str(exc))


@admin_notifications_bp.route("/dispatches/process-pending", methods=["POST"])
@require_superadmin()
def process_pending_notification_dispatches():
    try:
        body = request.get_json(silent=True) or {}
        limit = int(body.get("limit", 20))
    except (TypeError, ValueError):
        return api_error("invalid_limit", "limit must be an integer", status=400)

    try:
        registry = build_template_registry()
        with SqlAlchemyUnitOfWork() as uow:
            result = ProcessPendingNotificationDispatchesUseCase(
                uow,
                template_registry=registry,
            ).execute(limit=limit)

        return (
            jsonify(
                {
                    "processed": result.processed,
                    "completed": result.completed,
                    "failed": result.failed,
                    "errors": result.errors,
                }
            ),
            200,
        )
    except Exception as exc:
        return api_error("process_pending_failed", str(exc))


@integrations_notifications_bp.route("/process-pending", methods=["POST"])
@require_service_token()
@integration_rate_limit(key_prefix="notif-int-pending")
def integrations_process_pending_notification_dispatches():
    try:
        body = request.get_json(silent=True) or {}
        limit = int(body.get("limit", 20))
    except (TypeError, ValueError):
        return api_error("invalid_limit", "limit must be an integer", status=400)

    try:
        registry = build_template_registry()
        with SqlAlchemyUnitOfWork() as uow:
            result = ProcessPendingNotificationDispatchesUseCase(
                uow,
                template_registry=registry,
            ).execute(limit=limit)

        return (
            jsonify(
                {
                    "processed": result.processed,
                    "completed": result.completed,
                    "failed": result.failed,
                    "errors": result.errors,
                }
            ),
            200,
        )
    except Exception as exc:
        return api_error("process_pending_failed", str(exc))


@admin_notifications_bp.route("/templates", methods=["GET"])
@require_superadmin()
def list_notification_templates():
    try:
        items = ListNotificationTemplatesUseCase().execute()
        return jsonify(items), 200
    except Exception as exc:
        return api_error("list_templates_failed", str(exc))


@admin_notifications_bp.route("/templates", methods=["POST"])
@require_superadmin()
def create_notification_template():
    try:
        payload = request.get_json(silent=True) or {}
        item = CreateNotificationCustomTemplateUseCase().execute(payload)
        return jsonify(item), 201
    except ManageNotificationTemplatesValidationError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception as exc:
        return api_error("create_template_failed", str(exc))


@admin_notifications_bp.route("/templates/<template_id>", methods=["DELETE"])
@require_superadmin()
def delete_notification_template(template_id: str):
    try:
        DeleteNotificationCustomTemplateUseCase().execute(template_id)
        return jsonify({"ok": True}), 200
    except ManageNotificationTemplatesValidationError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception as exc:
        return api_error("delete_template_failed", str(exc))


@integrations_notifications_bp.route("/automation/birthdays", methods=["POST"])
@require_service_token()
@integration_rate_limit(key_prefix="notif-int-birthdays")
def integrations_process_birthday_notifications():
    try:
        with SqlAlchemyUnitOfWork() as uow:
            result = ProcessBirthdayNotificationsUseCase(uow).execute()

        return (
            jsonify(
                {
                    "eligible": result.eligible,
                    "sent": result.sent,
                    "skipped": result.skipped,
                }
            ),
            200,
        )
    except Exception as exc:
        return api_error("birthday_automation_failed", str(exc))


@integrations_notifications_bp.route("", methods=["POST"])
@require_service_token()
@integration_rate_limit(key_prefix="notif-int-dispatch")
def integrations_dispatch_notifications():
    try:
        body = request.get_json(silent=True) or {}
        request_dto = _parse_dispatch_body(body)
        scheduled_at = _parse_scheduled_at_from_body(body)
        return _dispatch_notifications(request_dto, scheduled_at=scheduled_at)
    except DispatchNotificationsValidationError as exc:
        return api_error("validation_error", str(exc), status=400)
    except Exception as exc:
        return api_error("dispatch_failed", str(exc))
