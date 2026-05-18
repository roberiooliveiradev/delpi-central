# app/domain/notifications/per_recipient_policy.py

from __future__ import annotations

from app.domain.notifications.notification_recipient_vars import template_requires_per_recipient_render
from app.domain.notifications.notification_templates import NotificationTemplateSpec
from app.domain.notifications.notification_variables import text_has_recipient_placeholders


def requires_per_recipient_render(
    *,
    presentation: str,
    template_spec: NotificationTemplateSpec | None,
    title: str | None,
    message: str | None,
    html_content: str | None,
    action_label: str | None,
) -> bool:
    if template_requires_per_recipient_render(template_spec):
        return True

    if (presentation or "").strip().lower() not in {"text", "html"}:
        return False

    return text_has_recipient_placeholders(title, message, html_content, action_label)
