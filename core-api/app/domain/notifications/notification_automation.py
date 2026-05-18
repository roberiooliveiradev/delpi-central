# app/domain/notifications/notification_automation.py

from app.application.dto.dispatch_notifications_request import DispatchNotificationsRequest
from app.domain.notifications.notification_templates import NOTIFICATION_TEMPLATES


def build_template_dispatch_request(
    *,
    template_id: str,
    user_ids: list[str],
    source_app: str = "notification-automation",
) -> DispatchNotificationsRequest:
    spec = NOTIFICATION_TEMPLATES.get(template_id)
    if not spec:
        raise ValueError(f"unknown template: {template_id}")

    return DispatchNotificationsRequest(
        title=spec.default_title,
        message=spec.default_message,
        type=spec.default_type,
        category=spec.category,
        presentation="template",
        html_content=None,
        action_type=None,
        action_label=None,
        action_target=None,
        icon=None,
        metadata={"templateId": template_id, "vars": {}},
        expires_at=None,
        broadcast=False,
        user_ids=user_ids,
        emails=[],
        role_ids=[],
        group_ids=[],
        source_app=source_app,
    )
