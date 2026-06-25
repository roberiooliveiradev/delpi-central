"""Acesso lazy à fachada — comentário operacional."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.chat_operational_data_commentary_service import (
        ChatOperationalDataCommentaryService,
    )


def commentary_service() -> type[ChatOperationalDataCommentaryService]:
    from app.domain.services.chat_operational_data_commentary_service import (
        ChatOperationalDataCommentaryService,
    )

    return ChatOperationalDataCommentaryService
