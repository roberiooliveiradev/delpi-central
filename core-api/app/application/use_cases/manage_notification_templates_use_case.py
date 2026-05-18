# app/application/use_cases/manage_notification_templates_use_case.py

from __future__ import annotations

from app.domain.notifications.notification_template_registry import NotificationTemplateRegistry
from app.domain.notifications.notification_variables import (
    ADMIN_VARIABLE_KEYS,
    RECIPIENT_VARIABLE_KEYS,
)
from app.extensions.db import db
from app.infrastructure.db.models.notification_custom_template import NotificationCustomTemplate


class ManageNotificationTemplatesValidationError(ValueError):
    pass


def build_template_registry() -> NotificationTemplateRegistry:
    rows = (
        NotificationCustomTemplate.query.filter_by(active=True)
        .order_by(NotificationCustomTemplate.created_at.desc())
        .all()
    )
    return NotificationTemplateRegistry(rows)


class ListNotificationTemplatesUseCase:
    def execute(self) -> list[dict]:
        return build_template_registry().list_public()


class CreateNotificationCustomTemplateUseCase:
    def execute(self, payload: dict) -> dict:
        label = (payload.get("label") or "").strip()
        if not label:
            raise ManageNotificationTemplatesValidationError("label is required")

        title_template = (payload.get("defaultTitle") or payload.get("title_template") or "").strip()
        message_template = (
            payload.get("defaultMessage") or payload.get("message_template") or ""
        ).strip()
        if not title_template or not message_template:
            raise ManageNotificationTemplatesValidationError(
                "defaultTitle and defaultMessage are required"
            )

        required_vars = _normalize_var_list(payload.get("requiredVars") or payload.get("required_vars"))
        optional_vars = _normalize_var_list(payload.get("optionalVars") or payload.get("optional_vars"))
        recipient_vars = _normalize_var_list(
            payload.get("recipientVars")
            or payload.get("recipient_vars")
            or payload.get("recipientAutoVars")
            or payload.get("recipient_auto_vars")
            or ["userName"]
        )

        _validate_var_keys(required_vars, optional_vars, recipient_vars)

        row = NotificationCustomTemplate(
            id=NotificationCustomTemplate.new_id(),
            label=label,
            category=(payload.get("category") or "custom").strip().lower(),
            default_type=(payload.get("defaultType") or payload.get("default_type") or "info").strip().lower(),
            title_template=title_template[:120],
            message_template=message_template[:500],
            layout={
                "hint": (payload.get("hint") or "").strip() or None,
                "fields": payload.get("fields") if isinstance(payload.get("fields"), list) else [],
            },
            required_vars=required_vars,
            optional_vars=optional_vars,
            recipient_vars=recipient_vars,
            active=True,
        )

        db.session.add(row)
        db.session.commit()

        from app.domain.notifications.notification_template_registry import spec_to_dict

        registry = build_template_registry()
        spec = registry.get(row.id)
        if not spec:
            raise ManageNotificationTemplatesValidationError("failed to load created template")
        return spec_to_dict(spec)


class DeleteNotificationCustomTemplateUseCase:
    def execute(self, template_id: str) -> None:
        template_id = (template_id or "").strip()
        if not template_id.startswith("custom_"):
            raise ManageNotificationTemplatesValidationError("only custom templates can be deleted")

        row = NotificationCustomTemplate.query.filter_by(id=template_id).first()
        if not row:
            raise ManageNotificationTemplatesValidationError("template not found")

        row.active = False
        db.session.commit()


def _normalize_var_list(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _validate_var_keys(required: list[str], optional: list[str], recipient: list[str]) -> None:
    allowed = ADMIN_VARIABLE_KEYS | RECIPIENT_VARIABLE_KEYS
    for key in required + optional + recipient:
        if key not in allowed:
            raise ManageNotificationTemplatesValidationError(f"unknown variable: {key}")
