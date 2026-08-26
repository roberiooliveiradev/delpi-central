"""Extrai ids de anexos referenciados no markdown da mensagem da sala."""

from __future__ import annotations

import re

from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)

_PENDING_PREFIX = "attachment:pending:"
_ATTACHMENT_PREFIX = "attachment:"


class InteractionMessageMarkdownAttachmentsService:
    """Lista uuids e pending ids citados em `![…](attachment:…)` no body_text."""

    @classmethod
    def list_attachment_refs(cls, body_text: str) -> tuple[str, ...]:
        """Retorna hrefs completos `attachment:…` na ordem de aparição (únicos)."""
        text = str(body_text or "")
        image_re = InteractionRoomContentService.markdown_image_pattern()
        allowed = InteractionRoomContentService.allowed_attachment_image_href_pattern()
        seen: set[str] = set()
        ordered: list[str] = []
        for match in image_re.finditer(text):
            href = str(match.group(2) or "").strip()
            if not allowed.fullmatch(href) or href in seen:
                continue
            seen.add(href)
            ordered.append(href)
        return tuple(ordered)

    @classmethod
    def list_attachment_ids(cls, body_text: str) -> tuple[str, ...]:
        """UUIDs persistidos (`attachment:{uuid}`), sem pending."""
        ids: list[str] = []
        for href in cls.list_attachment_refs(body_text):
            if href.startswith(_PENDING_PREFIX):
                continue
            if href.startswith(_ATTACHMENT_PREFIX):
                ids.append(href[len(_ATTACHMENT_PREFIX) :])
        return tuple(ids)

    @classmethod
    def list_pending_ids(cls, body_text: str) -> tuple[str, ...]:
        """Client ids após `attachment:pending:`."""
        pending: list[str] = []
        for href in cls.list_attachment_refs(body_text):
            if href.startswith(_PENDING_PREFIX):
                pending.append(href[len(_PENDING_PREFIX) :])
        return tuple(pending)

    @classmethod
    def rewrite_pending_to_attachment(
        cls, body_text: str, pending_to_uuid: dict[str, str]
    ) -> str:
        """Substitui `attachment:pending:{clientId}` por `attachment:{uuid}`."""
        text = str(body_text or "")
        if not pending_to_uuid:
            return text
        image_re = InteractionRoomContentService.markdown_image_pattern()

        def _replace(match: re.Match[str]) -> str:
            alt = match.group(1) or ""
            href = str(match.group(2) or "").strip()
            if not href.startswith(_PENDING_PREFIX):
                return match.group(0)
            client_id = href[len(_PENDING_PREFIX) :]
            uuid = str(pending_to_uuid.get(client_id) or "").strip()
            if not uuid:
                return match.group(0)
            return f"![{alt}]({_ATTACHMENT_PREFIX}{uuid})"

        return image_re.sub(_replace, text)

    @classmethod
    def rewrite_attachment_ids(
        cls, body_text: str, id_map: dict[str, str]
    ) -> str:
        """Substitui `attachment:{oldUuid}` por `attachment:{newUuid}`."""
        text = str(body_text or "")
        if not id_map:
            return text
        image_re = InteractionRoomContentService.markdown_image_pattern()

        def _replace(match: re.Match[str]) -> str:
            alt = match.group(1) or ""
            href = str(match.group(2) or "").strip()
            if not href.startswith(_ATTACHMENT_PREFIX) or href.startswith(_PENDING_PREFIX):
                return match.group(0)
            old_id = href[len(_ATTACHMENT_PREFIX) :]
            new_id = str(id_map.get(old_id) or "").strip()
            if not new_id:
                return match.group(0)
            return f"![{alt}]({_ATTACHMENT_PREFIX}{new_id})"

        return image_re.sub(_replace, text)
