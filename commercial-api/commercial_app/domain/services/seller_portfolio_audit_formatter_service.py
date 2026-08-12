from __future__ import annotations

import re
from typing import Any

from commercial_app.domain.entities.audit_log_entry import AuditLogEntry
from commercial_app.domain.services.audit_messages_content_service import (
    AuditMessagesContentService,
)

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _as_str(value: Any, default: str = "—") -> str:
    text = str(value).strip() if value is not None else ""
    return text or default


def _looks_like_technical_id(value: str) -> bool:
    cleaned = (value or "").strip()
    if not cleaned:
        return True
    if _UUID_RE.match(cleaned):
        return True
    return False


def _human_label(
    *,
    explicit: Any,
    raw_id: Any,
    fallback: str,
) -> str:
    for candidate in (explicit,):
        text = str(candidate).strip() if candidate is not None else ""
        if text and not _looks_like_technical_id(text):
            return text
    raw = str(raw_id).strip() if raw_id is not None else ""
    if raw and not _looks_like_technical_id(raw):
        return raw
    return fallback


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
        elif payload.get("member_count") is not None:
            member_count = _as_str(payload.get("member_count"), "0")
        customer_code = str(payload.get("customer_code") or "").strip()
        customer_store = str(payload.get("customer_store") or "").strip()
        customer_name = str(payload.get("customer_name") or "").strip()
        customer_label = customer_name or (
            f"{customer_code}/{customer_store}" if customer_code and customer_store else "—"
        )
        anonymous_user = self._content.anonymous_user_label()
        anonymous_portfolio = self._content.anonymous_portfolio_label()
        user_label = _human_label(
            explicit=payload.get("user_display_name") or payload.get("user_label"),
            raw_id=payload.get("user_id"),
            fallback=anonymous_user,
        )
        source_label = _human_label(
            explicit=payload.get("source_display_name")
            or payload.get("source_portfolio_label"),
            raw_id=payload.get("source_portfolio_id"),
            fallback=anonymous_portfolio,
        )
        target_label = _human_label(
            explicit=payload.get("target_display_name")
            or payload.get("target_portfolio_label"),
            raw_id=payload.get("target_portfolio_id"),
            fallback=anonymous_portfolio,
        )
        return {
            "action": entry.action,
            "user_id": _as_str(payload.get("user_id")),
            "user_label": user_label,
            "role": role,
            "role_label": self._content.role_label(role),
            "member_count": member_count,
            "display_name": _as_str(payload.get("display_name"), "carteira"),
            "previous_display_name": _as_str(payload.get("previous_display_name"), "—"),
            "customer_count": _as_str(payload.get("customer_count"), "0"),
            "customer_code": customer_code or "—",
            "customer_store": customer_store or "—",
            "customer_name": customer_name or "—",
            "customer_label": customer_label,
            "transferred_count": _as_str(payload.get("transferred_count"), "0"),
            "failed_count": _as_str(payload.get("failed_count"), "0"),
            "source_portfolio_id": _as_str(payload.get("source_portfolio_id")),
            "target_portfolio_id": _as_str(payload.get("target_portfolio_id")),
            "source_portfolio_label": source_label,
            "target_portfolio_label": target_label,
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
