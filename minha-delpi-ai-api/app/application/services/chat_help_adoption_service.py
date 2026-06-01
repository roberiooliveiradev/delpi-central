"""Métricas leves de adoção do painel de ajuda — Autoajuda Fase 5."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("minha-delpi-ai-api.help-adoption")

_ALLOWED_EVENTS = frozenset(
    {
        "help_panel_open",
        "help_panel_search",
        "help_highlight_click",
        "help_quick_prompt",
        "self_help_requested",
        "self_help_feedback",
        "self_help_suggestion_clicked",
    }
)


class ChatHelpAdoptionService:
    @classmethod
    def record(cls, *, user_id: str, event: str, metadata: dict[str, Any] | None = None) -> dict:
        token = str(event or "").strip()

        if token not in _ALLOWED_EVENTS:
            raise ValueError(f"evento inválido: {token}")

        safe_meta = metadata if isinstance(metadata, dict) else {}

        logger.info(
            "help_adoption event=%s user_id=%s metadata=%s",
            token,
            str(user_id).strip(),
            safe_meta,
        )

        return {"ok": True, "event": token}
