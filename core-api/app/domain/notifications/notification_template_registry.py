# app/domain/notifications/notification_template_registry.py

from __future__ import annotations

from dataclasses import dataclass

from app.domain.notifications.notification_templates import (
    NOTIFICATION_TEMPLATES,
    NotificationTemplateSpec,
)


@dataclass(frozen=True)
class NotificationTemplateFieldSpec:
    key: str
    label: str
    placeholder: str | None = None
    required: bool = False


def _fields_from_spec(spec: NotificationTemplateSpec) -> tuple[NotificationTemplateFieldSpec, ...]:
    fields: list[NotificationTemplateFieldSpec] = []
    labels = {
        "eventName": "Nome do evento",
        "eventDate": "Data",
        "location": "Local",
        "appNames": "Aplicações",
    }
    for key in spec.required_vars:
        fields.append(
            NotificationTemplateFieldSpec(
                key=key,
                label=labels.get(key, key),
                required=True,
            )
        )
    for key in spec.optional_vars:
        fields.append(
            NotificationTemplateFieldSpec(
                key=key,
                label=labels.get(key, key),
                required=False,
            )
        )
    return tuple(fields)


def spec_to_dict(spec: NotificationTemplateSpec) -> dict:
    return {
        "id": spec.id,
        "label": spec.label,
        "category": spec.category,
        "defaultType": spec.default_type,
        "defaultTitle": spec.default_title,
        "defaultMessage": spec.default_message,
        "requiredVars": list(spec.required_vars),
        "optionalVars": list(spec.optional_vars),
        "recipientVars": list(spec.recipient_vars),
        "recipientAutoVars": list(spec.recipient_vars),
        "isSystem": spec.is_system,
        "hint": spec.hint,
        "fields": [
            {
                "key": field.key,
                "label": field.label,
                "placeholder": field.placeholder,
                "required": field.required,
            }
            for field in _fields_from_spec(spec)
        ],
    }


def custom_row_to_spec(row) -> NotificationTemplateSpec:
    layout = row.layout if isinstance(row.layout, dict) else {}
    return NotificationTemplateSpec(
        id=row.id,
        label=row.label,
        category=row.category,
        default_type=row.default_type,
        default_title=row.title_template,
        default_message=row.message_template,
        required_vars=tuple(row.required_vars or []),
        optional_vars=tuple(row.optional_vars or []),
        recipient_vars=tuple(row.recipient_vars or []),
        is_system=False,
        hint=layout.get("hint"),
    )


class NotificationTemplateRegistry:
    def __init__(self, custom_rows: list | None = None):
        self._custom_specs: dict[str, NotificationTemplateSpec] = {}
        self._custom_rows: dict[str, object] = {}
        for row in custom_rows or []:
            if not row.active:
                continue
            spec = custom_row_to_spec(row)
            self._custom_specs[spec.id] = spec
            self._custom_rows[spec.id] = row

    def get_custom_layout(self, template_id: str) -> dict:
        row = self._custom_rows.get(template_id)
        if row is None:
            return {}
        layout = getattr(row, "layout", None)
        return layout if isinstance(layout, dict) else {}

    def get(self, template_id: str) -> NotificationTemplateSpec | None:
        template_id = (template_id or "").strip()
        if template_id in NOTIFICATION_TEMPLATES:
            return NOTIFICATION_TEMPLATES[template_id]
        return self._custom_specs.get(template_id)

    def list_all(self) -> list[NotificationTemplateSpec]:
        return list(NOTIFICATION_TEMPLATES.values()) + list(self._custom_specs.values())

    def list_public(self) -> list[dict]:
        items: list[dict] = []
        for spec in NOTIFICATION_TEMPLATES.values():
            items.append(spec_to_dict(spec))
        for template_id, spec in self._custom_specs.items():
            data = spec_to_dict(spec)
            layout = self.get_custom_layout(template_id)
            if layout.get("fields"):
                data["fields"] = layout["fields"]
            if layout.get("hint"):
                data["hint"] = layout["hint"]
            items.append(data)
        return sorted(items, key=lambda item: (not item.get("isSystem"), item.get("label", "").lower()))
