"""Acesso lazy à fachada — perfis de apresentação."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.chat_presentation_profile_service import (
        ChatPresentationProfileService,
    )


def presentation_profile_service() -> type[ChatPresentationProfileService]:
    from app.domain.services.chat_presentation_profile_service import (
        ChatPresentationProfileService,
    )

    return ChatPresentationProfileService
