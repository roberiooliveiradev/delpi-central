"""Seleção declarativa de tools internas da plataforma — bundle ``platform_tools``."""

from __future__ import annotations

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_platform_tools_content_service import (
    ChatPlatformToolsContentService,
)


class ChatPlatformToolSelectionService:
    @classmethod
    def portal_routes_terms(cls) -> tuple[str, ...]:
        return ChatPlatformToolsContentService.list("toolSelection", "portalRoutesTerms")

    @classmethod
    def portal_routes_reason(cls) -> str:
        return ChatPlatformToolsContentService.get(
            "toolSelection",
            "portalRoutesReason",
            default="A pergunta solicita menus ou páginas autorizadas no portal DELPI.",
        )

    @classmethod
    def matches_portal_routes_inquiry(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        return any(term in normalized for term in cls.portal_routes_terms())
