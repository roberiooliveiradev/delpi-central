# app/interfaces/http/serializers/notification_dispatch_serializer.py

from app.application.dto.notification_dispatch_response import NotificationDispatchResponse
from app.domain.ports.notification_dispatch_repository import NotificationDispatchDTO


def serialize_notification_dispatch(
    dto: NotificationDispatchDTO,
    *,
    include_payload: bool = False,
) -> dict:
    result = {
        "id": str(dto.id),
        "createdByUserId": dto.created_by_user_id,
        "status": dto.status,
        "scheduledAt": dto.scheduled_at.isoformat() + "Z" if dto.scheduled_at else None,
        "processedAt": dto.processed_at.isoformat() + "Z" if dto.processed_at else None,
        "broadcast": dto.broadcast,
        "recipientCount": dto.recipient_count,
        "createdCount": dto.created_count,
        "title": dto.title,
        "category": dto.category,
        "presentation": dto.presentation,
        "templateId": dto.template_id,
        "sourceApp": dto.source_app,
        "errorMessage": dto.error_message,
        "createdAt": dto.created_at.isoformat() + "Z" if dto.created_at else None,
    }
    if include_payload:
        result["payload"] = dto.payload or {}
    return result


def serialize_dispatch_result(result: NotificationDispatchResponse) -> dict:
    return {
        "dispatchId": result.dispatch_id,
        "status": result.status,
        "scheduledAt": result.scheduled_at,
        "createdCount": result.created_count,
        "notificationIds": result.notification_ids,
        "recipientCount": result.recipient_count,
        "errorMessage": result.error_message,
    }
