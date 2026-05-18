# app/interfaces/http/serializers/notification_serializer.py

from app.domain.ports.notification_repository import NotificationDTO


def serialize_notification(notification: NotificationDTO) -> dict:
    payload = {
        "id": str(notification.id) if notification.id else "",
        "user_id": str(notification.user_id),
        "title": notification.title,
        "message": notification.message,
        "type": notification.type,
        "category": notification.category,
        "presentation": notification.presentation,
        "htmlContent": notification.html_content,
        "icon": notification.icon,
        "metadata": notification.metadata,
        "read": notification.read,
        "createdAt": notification.created_at.isoformat() + "Z",
    }

    if notification.action_type:
        payload["action"] = {
            "type": notification.action_type,
            "label": notification.action_label,
            "target": notification.action_target,
        }
    else:
        payload["action"] = None

    if notification.expires_at:
        payload["expiresAt"] = notification.expires_at.isoformat() + "Z"
    else:
        payload["expiresAt"] = None

    return payload
