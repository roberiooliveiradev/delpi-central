"""Extract http(s) links and assemble shared-item dicts for a room (pure domain)."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Sequence
from urllib.parse import urlparse
from uuid import UUID

from commercial_app.domain.entities.attachment import CommercialAttachment
from commercial_app.domain.entities.interaction_room import InteractionMessage

_MARKDOWN_LINK = re.compile(
    r"\[([^\]]*)\]\((https?://[^)\s]+)\)",
    re.IGNORECASE,
)
_BARE_URL = re.compile(
    r"(?<!\()(?<!\]\()(https?://[^\s<>\[\]()\"']+)",
    re.IGNORECASE,
)


class InteractionRoomSharedItemsService:
    """Build file + link shared items from messages and attachments."""

    @classmethod
    def extract_http_links(cls, body_text: str) -> list[tuple[str, str]]:
        """Return list of (title, href) preserving first-seen order."""
        text = str(body_text or "")
        seen: set[str] = set()
        out: list[tuple[str, str]] = []
        covered_spans: list[tuple[int, int]] = []

        for match in _MARKDOWN_LINK.finditer(text):
            title = (match.group(1) or "").strip() or cls._host_label(match.group(2))
            href = match.group(2).rstrip(".,;)")
            covered_spans.append(match.span())
            key = href.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append((title, href))

        for match in _BARE_URL.finditer(text):
            start, end = match.span()
            if any(cs <= start < ce or cs < end <= ce for cs, ce in covered_spans):
                continue
            href = match.group(1).rstrip(".,;)")
            key = href.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append((cls._host_label(href), href))
        return out

    @staticmethod
    def _host_label(href: str) -> str:
        try:
            host = (urlparse(href).hostname or "").strip()
            return host or href
        except Exception:
            return href

    @classmethod
    def link_item_id(cls, message_id: UUID, href: str) -> str:
        digest = hashlib.sha1(f"{message_id}:{href}".encode("utf-8")).hexdigest()[:16]
        return f"link-{digest}"

    @classmethod
    def file_item(
        cls,
        *,
        attachment: CommercialAttachment,
        message_id: UUID,
    ) -> dict[str, Any]:
        return {
            "id": str(attachment.id),
            "kind": "file",
            "title": attachment.file_name,
            "subtitle": attachment.content_type or None,
            "shared_at": cls._iso(attachment.created_at),
            "shared_by": attachment.uploaded_by_user_id or None,
            "message_id": str(message_id),
            "attachment_id": str(attachment.id),
            "href": None,
        }

    @classmethod
    def link_item(
        cls,
        *,
        message: InteractionMessage,
        title: str,
        href: str,
    ) -> dict[str, Any]:
        return {
            "id": cls.link_item_id(message.id, href),
            "kind": "link",
            "title": title,
            "subtitle": cls._host_label(href),
            "shared_at": cls._iso(message.created_at),
            "shared_by": message.author_user_id or None,
            "message_id": str(message.id),
            "attachment_id": None,
            "href": href,
        }

    @staticmethod
    def _iso(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.isoformat()

    @classmethod
    def assemble(
        cls,
        *,
        messages: Sequence[InteractionMessage],
        attachments_by_message_id: dict[str, Sequence[CommercialAttachment]],
        kind: str,
        query: str | None,
    ) -> list[dict[str, Any]]:
        kind_norm = (kind or "all").strip().lower()
        if kind_norm not in {"all", "file", "link"}:
            kind_norm = "all"
        q = (query or "").strip().lower()

        items: list[dict[str, Any]] = []
        for message in messages:
            mid = str(message.id)
            if kind_norm in {"all", "file"}:
                for attachment in attachments_by_message_id.get(mid, ()):
                    items.append(cls.file_item(attachment=attachment, message_id=message.id))
            if kind_norm in {"all", "link"}:
                for title, href in cls.extract_http_links(message.body_text):
                    items.append(cls.link_item(message=message, title=title, href=href))

        if q:
            items = [
                item
                for item in items
                if q in str(item.get("title") or "").lower()
                or q in str(item.get("subtitle") or "").lower()
                or q in str(item.get("href") or "").lower()
            ]

        items.sort(key=lambda row: str(row.get("shared_at") or ""), reverse=True)
        return items
