"""Chips de refinamento após geração de e-mail corporativo."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.domain.services.chat_email_intent_service import ChatEmailIntentService
from app.domain.services.chat_email_quality_validator import ChatEmailQualityValidator
from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatEmailFollowUpService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str | None = None,
        answer: str | None = None,
        workspace_context: dict | None = None,
    ) -> None:
        if not ChatEmailIntentService.is_email_writing(message):
            if not (workspace_context or {}).get("emailWritingMode"):
                return

        ctx = ChatEmailIntentService.extract_context(message)
        subtype = ctx.get("subtype")
        suggestions = cls.build_suggestions(subtype)

        if suggestions:
            metadata["emailFollowUpSuggestions"] = suggestions

        text_task = ChatEmailIntentService.build_text_task_metadata(
            message=message,
            answer=answer,
        )

        if text_task:
            metadata.update(text_task)

        quality = ChatEmailQualityValidator.validate(
            answer,
            user_message=message,
            expected_tone=ctx.get("tone"),
            user_provided_signature=ctx.get("senderSignature"),
        )

        if quality.get("checks"):
            metadata["emailQuality"] = quality

    @classmethod
    def merge_guard_metadata(cls, metadata: dict, guard_meta: dict[str, Any] | None) -> None:
        if not guard_meta:
            return

        metadata.update(guard_meta)

        guard = guard_meta.get("emailGuard") or {}
        quality = guard.get("quality")

        if isinstance(quality, dict):
            metadata["emailQuality"] = quality

    @classmethod
    def build_suggestions(cls, subtype: str | None = None) -> list[dict[str, str]]:
        labels = list(
            _playbook().get("emailFollowUpChips")
            or [
                "Deixar mais formal",
                "Deixar mais curto",
                "Tom mais executivo",
                "Tom mais cordial",
                "Tom mais firme",
                "Criar assunto alternativo",
                "Transformar em WhatsApp",
                "Traduzir para inglês",
                "Colocar na lousa",
            ]
        )

        if subtype == "email_subjects":
            labels = [
                label
                for label in labels
                if label not in {"Criar assunto alternativo"}
            ][:6]

        queries = _playbook().get("emailFollowUpQueries") or {}
        suggestions: list[dict[str, str]] = []

        for label in labels[:10]:
            template = str(queries.get(label) or label).strip()
            suggestions.append({"label": str(label), "query": template})

        return suggestions
