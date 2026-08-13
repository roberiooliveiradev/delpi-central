from __future__ import annotations

from typing import Any

from commercial_app.domain.entities.audit_log_entry import AuditLogEntry
from commercial_app.domain.services.audit_messages_content_service import (
    AuditMessagesContentService,
)


def _as_str(value: Any, default: str = "—") -> str:
    text = str(value).strip() if value is not None else ""
    return text or default


def _format_template(template: str, values: dict[str, str]) -> str:
    class _Safe(dict[str, str]):
        def __missing__(self, key: str) -> str:
            return "—"

    try:
        return template.format_map(_Safe(values))
    except Exception:
        return template


class AccountAuditFormatterService:
    """Monta título/mensagem/tom legíveis para eventos de Conta (contatos, avatar)."""

    def __init__(self, content: type[AuditMessagesContentService] | None = None) -> None:
        self._content = content or AuditMessagesContentService

    def _context(self, entry: AuditLogEntry) -> dict[str, str]:
        payload = entry.payload if isinstance(entry.payload, dict) else {}
        full_name = _as_str(payload.get("full_name"), "contato")
        channel = _as_str(payload.get("channel"), "—")
        explicit_fields = str(payload.get("fields_label") or "").strip()
        if explicit_fields:
            fields_label = explicit_fields
        else:
            changed_fields = payload.get("changed_fields")
            if isinstance(changed_fields, list) and changed_fields:
                fields_label = ", ".join(str(item) for item in changed_fields if item)
            else:
                fields_label = "dados"
        return {
            "action": entry.action,
            "full_name": full_name,
            "channel": channel,
            "fields_label": fields_label or "dados",
            "contact_id": _as_str(payload.get("contact_id")),
        }

    def format_entry(self, entry: AuditLogEntry) -> dict[str, Any]:
        ctx = self._context(entry)
        title = self._content.title_for(entry.action)
        message = _format_template(self._content.message_template_for(entry.action), ctx)
        created = entry.created_at.isoformat() if entry.created_at is not None else None
        return {
            "id": entry.id,
            "action": entry.action,
            "actor_user_id": entry.actor_user_id,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "payload": dict(entry.payload or {}),
            "created_at": created,
            "title": title,
            "message": message,
            "tone": self._content.tone_for(entry.action),
        }
