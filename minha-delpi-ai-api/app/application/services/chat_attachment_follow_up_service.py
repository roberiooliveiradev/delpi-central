"""Sugestões após envio de anexo (Playbook 07 — anexos e arquivos)."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatAttachmentFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        had_attachments: bool,
    ) -> None:
        if not had_attachments:
            return

        labels = _playbook().get("attachmentFollowUpChips") or [
            "Resumir",
            "Corrigir",
            "Traduzir",
            "Extrair pendências",
        ]
        queries = _playbook().get("attachmentFollowUpQueries") or {}

        suggestions: list[dict[str, str]] = []

        for label in labels[:6]:
            template = str(queries.get(label) or label).strip()
            suggestions.append({"label": str(label), "query": template})

        if suggestions:
            metadata["attachmentFollowUpSuggestions"] = suggestions
