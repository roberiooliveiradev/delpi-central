# app/application/services/notification_content_service.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

import bleach

from app.domain.notifications.notification_constants import (
    ALLOWED_ACTION_TYPES,
    ALLOWED_NOTIFICATION_CATEGORIES,
    ALLOWED_NOTIFICATION_TYPES,
    ALLOWED_PRESENTATION_MODES,
    CATEGORY_DEFAULT_ICONS,
)
from app.domain.notifications.notification_templates import NotificationTemplateSpec
from app.domain.notifications.notification_variables import ALL_KNOWN_VARIABLE_KEYS
from app.domain.notifications.template_rendering import TemplateRenderError, render_template_text


class NotificationContentValidationError(ValueError):
    pass


ALLOWED_HTML_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "b",
    "i",
    "ul",
    "ol",
    "li",
    "a",
    "h3",
    "h4",
    "span",
]

ALLOWED_HTML_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "span": ["class"],
}


@dataclass(frozen=True)
class NotificationActionDTO:
    type: str
    label: str | None
    target: str | None


@dataclass(frozen=True)
class PreparedNotificationContent:
    title: str | None
    message: str
    type: str
    category: str
    presentation: str
    html_content: str | None
    action_type: str | None
    action_label: str | None
    action_target: str | None
    icon: str | None
    metadata: dict | None
    expires_at: datetime | None


class NotificationContentService:

    def prepare(
        self,
        *,
        title: str | None,
        message: str,
        type: str,
        category: str,
        presentation: str,
        html_content: str | None,
        action_type: str | None,
        action_label: str | None,
        action_target: str | None,
        icon: str | None,
        metadata: dict | None,
        expires_at: datetime | None,
        recipient_context: dict[str, str] | None = None,
        template_spec: NotificationTemplateSpec | None = None,
    ) -> PreparedNotificationContent:
        normalized_presentation = (presentation or "text").strip().lower()
        if normalized_presentation not in ALLOWED_PRESENTATION_MODES:
            raise NotificationContentValidationError(
                f"presentation must be one of: {', '.join(sorted(ALLOWED_PRESENTATION_MODES))}"
            )

        if metadata is not None and not isinstance(metadata, dict):
            raise NotificationContentValidationError("metadata must be an object")

        if normalized_presentation == "template":
            if template_spec is None:
                raise NotificationContentValidationError("template_spec is required for template presentation")
            template_context = self._prepare_template(
                metadata or {},
                category,
                type,
                title,
                message,
                spec=template_spec,
                recipient_context=recipient_context,
            )
            normalized_category = template_context["category"]
            notification_type = template_context["type"]
            normalized_title = template_context["title"]
            normalized_message = template_context["message"]
            metadata = template_context["metadata"]
        else:
            normalized_message = (message or "").strip()
            if not normalized_message:
                raise NotificationContentValidationError("message is required")

            if len(normalized_message) > 500:
                raise NotificationContentValidationError("message must be at most 500 characters")

            normalized_title = title.strip() if title else None
            if normalized_title and len(normalized_title) > 120:
                raise NotificationContentValidationError("title must be at most 120 characters")

            notification_type = (type or "info").strip().lower()
            if notification_type not in ALLOWED_NOTIFICATION_TYPES:
                raise NotificationContentValidationError(
                    f"type must be one of: {', '.join(sorted(ALLOWED_NOTIFICATION_TYPES))}"
                )

            normalized_category = (category or "system").strip().lower()
            if normalized_category not in ALLOWED_NOTIFICATION_CATEGORIES:
                raise NotificationContentValidationError(
                    f"category must be one of: {', '.join(sorted(ALLOWED_NOTIFICATION_CATEGORIES))}"
                )

        if recipient_context and normalized_presentation in {"text", "html"}:
            try:
                if normalized_title:
                    normalized_title = render_template_text(normalized_title, recipient_context)
                normalized_message = render_template_text(normalized_message, recipient_context)
            except TemplateRenderError as exc:
                raise NotificationContentValidationError(str(exc)) from exc

        sanitized_html = None
        if normalized_presentation == "html":
            raw_html = (html_content or "").strip()
            if not raw_html:
                raise NotificationContentValidationError(
                    "htmlContent is required when presentation is html"
                )
            if recipient_context:
                try:
                    raw_html = render_template_text(raw_html, recipient_context)
                except TemplateRenderError as exc:
                    raise NotificationContentValidationError(str(exc)) from exc
            sanitized_html = self._sanitize_html(raw_html)
            if not sanitized_html:
                raise NotificationContentValidationError("htmlContent is empty after sanitization")

        action = self._normalize_action(action_type, action_label, action_target)

        normalized_icon = (icon or "").strip() or CATEGORY_DEFAULT_ICONS.get(normalized_category)

        if recipient_context and normalized_presentation == "html":
            action_label_rendered = action.label
            if action.label:
                try:
                    action_label_rendered = render_template_text(action.label, recipient_context)
                except TemplateRenderError:
                    action_label_rendered = action.label
            action = NotificationActionDTO(
                type=action.type,
                label=action_label_rendered,
                target=action.target,
            )

        return PreparedNotificationContent(
            title=normalized_title,
            message=normalized_message,
            type=notification_type,
            category=normalized_category,
            presentation=normalized_presentation,
            html_content=sanitized_html,
            action_type=action.type if action.type != "none" else None,
            action_label=action.label,
            action_target=action.target,
            icon=normalized_icon,
            metadata=metadata,
            expires_at=expires_at,
        )

    def _sanitize_html(self, raw_html: str) -> str:
        cleaned = bleach.clean(
            raw_html,
            tags=ALLOWED_HTML_TAGS,
            attributes=ALLOWED_HTML_ATTRIBUTES,
            protocols=["http", "https", "mailto"],
            strip=True,
        )
        return cleaned.strip()

    def _normalize_action(
        self,
        action_type: str | None,
        action_label: str | None,
        action_target: str | None,
    ) -> NotificationActionDTO:
        normalized_type = (action_type or "none").strip().lower()
        if normalized_type not in ALLOWED_ACTION_TYPES:
            raise NotificationContentValidationError(
                f"action.type must be one of: {', '.join(sorted(ALLOWED_ACTION_TYPES))}"
            )

        label = action_label.strip() if action_label else None
        target = action_target.strip() if action_target else None

        if normalized_type == "none":
            return NotificationActionDTO(type="none", label=None, target=None)

        if not target:
            raise NotificationContentValidationError("action.target is required when action is set")

        if normalized_type == "portal_route":
            if not target.startswith("/"):
                raise NotificationContentValidationError(
                    "action.target for portal_route must start with /"
                )
            if target.startswith("//"):
                raise NotificationContentValidationError("action.target must be a relative portal path")

        if normalized_type == "external_url":
            parsed = urlparse(target)
            if parsed.scheme != "https" or not parsed.netloc:
                raise NotificationContentValidationError(
                    "action.target for external_url must be a valid https URL"
                )

        if not label:
            label = "Abrir"

        if len(label) > 80:
            raise NotificationContentValidationError("action.label must be at most 80 characters")

        if len(target) > 500:
            raise NotificationContentValidationError("action.target must be at most 500 characters")

        return NotificationActionDTO(type=normalized_type, label=label, target=target)

    def _prepare_template(
        self,
        metadata: dict,
        category: str,
        notification_type: str,
        title: str | None,
        message: str,
        *,
        spec: NotificationTemplateSpec,
        recipient_context: dict[str, str] | None = None,
    ) -> dict:
        template_id = spec.id

        raw_vars = metadata.get("vars") or metadata.get("templateVars") or {}
        if not isinstance(raw_vars, dict):
            raise NotificationContentValidationError("metadata.vars must be an object")

        request_vars: dict[str, str] = {}
        for key, value in raw_vars.items():
            if value is None:
                continue
            text = str(value).strip()
            if text:
                request_vars[str(key)] = text

        recipient_vars: dict[str, str] = {}
        if recipient_context:
            for key, value in recipient_context.items():
                if value is None:
                    continue
                text = str(value).strip()
                if text:
                    recipient_vars[str(key)] = text

        vars_normalized = {**recipient_vars, **request_vars}

        for required_key in spec.required_vars:
            if required_key not in vars_normalized:
                raise NotificationContentValidationError(
                    f"template var '{required_key}' is required for {template_id}"
                )

        for recipient_key in spec.recipient_vars:
            if recipient_key not in vars_normalized:
                raise NotificationContentValidationError(
                    f"template var '{recipient_key}' could not be resolved for recipient"
                )

        allowed_keys = (
            set(spec.required_vars)
            | set(spec.optional_vars)
            | set(spec.recipient_vars)
            | ALL_KNOWN_VARIABLE_KEYS
        )
        for key in vars_normalized:
            if key not in allowed_keys:
                raise NotificationContentValidationError(
                    f"unknown template var '{key}' for {template_id}"
                )

        rendered_title = (title or "").strip() or spec.default_title
        rendered_message = (message or "").strip() or spec.default_message

        try:
            rendered_title = render_template_text(rendered_title, vars_normalized)
            rendered_message = render_template_text(rendered_message, vars_normalized)
        except TemplateRenderError as exc:
            raise NotificationContentValidationError(str(exc)) from exc

        if len(rendered_message) > 500:
            raise NotificationContentValidationError("rendered message must be at most 500 characters")

        normalized_category = (category or spec.category).strip().lower()
        if normalized_category not in ALLOWED_NOTIFICATION_CATEGORIES:
            normalized_category = spec.category

        normalized_type = (notification_type or spec.default_type).strip().lower()
        if normalized_type not in ALLOWED_NOTIFICATION_TYPES:
            normalized_type = spec.default_type

        return {
            "category": normalized_category,
            "type": normalized_type,
            "title": rendered_title[:120] if rendered_title else None,
            "message": rendered_message,
            "metadata": {
                "templateId": template_id,
                "vars": vars_normalized,
            },
        }
