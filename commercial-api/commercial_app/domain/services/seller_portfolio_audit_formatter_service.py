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


class SellerPortfolioAuditFormatterService:
    """Monta título/mensagem/tom legíveis a partir de action + payload."""

    def __init__(self, content: type[AuditMessagesContentService] | None = None) -> None:
        self._content = content or AuditMessagesContentService

    def _context(self, entry: AuditLogEntry) -> dict[str, str]:
        payload = entry.payload if isinstance(entry.payload, dict) else {}
        role = _as_str(payload.get("role"), "member")
        members = payload.get("members")
        member_count = "0"
        if isinstance(members, list):
            member_count = str(len(members))
        return {
            "action": entry.action,
            "user_id": _as_str(payload.get("user_id")),
            "role": role,
            "role_label": self._content.role_label(role),
            "member_count": member_count,
            "display_name": _as_str(payload.get("display_name"), "carteira"),
            "customer_count": _as_str(payload.get("customer_count"), "0"),
            "transferred_count": _as_str(payload.get("transferred_count"), "0"),
            "source_portfolio_id": _as_str(payload.get("source_portfolio_id")),
            "target_portfolio_id": _as_str(payload.get("target_portfolio_id")),
            "reason_note": _as_str(payload.get("reason_note")),
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
