"""Política de body_text da mensagem: markdown com inline permitido; sem HTML cru."""

from __future__ import annotations

import re

from commercial_app.domain.services.interaction_room_content_service import (
    InteractionRoomContentService,
)

_ALLOWED_STRIPPERS = (
    re.compile(r"</?u>", re.IGNORECASE),
    re.compile(r'<span\s+style="font-size:\s*\d+px"\s*>', re.IGNORECASE),
    re.compile(r"</span>", re.IGNORECASE),
)
_HTML_TAG_PROBE = re.compile(r"<[a-zA-Z!/?]")


class InteractionMessageBodyPolicyService:
    """Rejeita HTML cru em body_text; permite `<u>` e span de fonte do composer."""

    @classmethod
    def assert_markdown_body(cls, body_text: str) -> None:
        if cls.contains_raw_html(body_text):
            raise ValueError(InteractionRoomContentService.error("bodyHtmlNotAllowed"))

    @classmethod
    def contains_raw_html(cls, body_text: str) -> bool:
        text = str(body_text or "")
        if "<" not in text:
            return False
        cleaned = text
        for pattern in _ALLOWED_STRIPPERS:
            cleaned = pattern.sub("", cleaned)
        return bool(_HTML_TAG_PROBE.search(cleaned))
