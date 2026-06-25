"""Acesso lazy à fachada — intenção de consulta de produto."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.chat_product_query_intent_service import (
        ChatProductQueryIntentService,
    )


def intent_service() -> type[ChatProductQueryIntentService]:
    from app.domain.services.chat_product_query_intent_service import (
        ChatProductQueryIntentService,
    )

    return ChatProductQueryIntentService
