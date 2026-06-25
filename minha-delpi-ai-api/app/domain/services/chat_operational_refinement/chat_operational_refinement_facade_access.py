"""Acesso lazy à fachada — refinamento operacional."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.chat_operational_refinement_service import (
        ChatOperationalRefinementService,
    )


def refinement_service() -> type[ChatOperationalRefinementService]:
    from app.domain.services.chat_operational_refinement_service import (
        ChatOperationalRefinementService,
    )

    return ChatOperationalRefinementService
