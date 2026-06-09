"""Extrai texto fonte e referências — playbook editor §38 (TextContextResolver)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_text_context_vocabulary_service import (
    ChatTextContextVocabularyService,
)


class ChatTextContextResolverService:
    @classmethod
    def _previous_reference_terms(cls) -> tuple[str, ...]:
        return ChatTextContextVocabularyService.terms("previousReferenceTerms")

    @classmethod
    def _canvas_markers(cls) -> tuple[str, ...]:
        return ChatTextContextVocabularyService.terms("canvasMarkers")

    @classmethod
    def _attachment_markers(cls) -> tuple[str, ...]:
        return ChatTextContextVocabularyService.terms("attachmentMarkers")

    @classmethod
    def _inline_extract_verbs(cls) -> tuple[str, ...]:
        return ChatTextContextVocabularyService.terms("inlineExtractVerbs")

    @classmethod
    def resolve(
        cls,
        message: str | None,
        *,
        previous_messages: list | None = None,
    ) -> dict[str, Any]:
        raw = (message or "").strip()
        normalized = raw.lower()

        extracted = cls._extract_inline_text(raw)
        references_previous = any(ref in normalized for ref in cls._previous_reference_terms())
        references_canvas = any(token in normalized for token in cls._canvas_markers())
        references_attachment = any(
            token in normalized for token in cls._attachment_markers()
        )

        prior_snippet = None

        if references_previous and previous_messages:
            prior_snippet = cls._latest_assistant_snippet(previous_messages)

        return {
            "hasInlineText": bool(extracted),
            "inlineText": extracted,
            "referencesPrevious": references_previous,
            "referencesCanvas": references_canvas,
            "referencesAttachment": references_attachment,
            "priorSnippet": prior_snippet,
        }

    @classmethod
    def format_prompt_block(cls, context: dict[str, Any] | None) -> str | None:
        if not isinstance(context, dict):
            return None

        lines: list[str] = []

        if context.get("inlineText"):
            snippet = str(context["inlineText"]).strip()

            if len(snippet) > 4000:
                snippet = snippet[:4000] + "…"

            lines.append(
                ChatTextContextVocabularyService.text(
                    "promptBlock",
                    "inlineTextSource",
                    snippet=snippet,
                )
            )

        if context.get("priorSnippet") and context.get("referencesPrevious"):
            prior = str(context["priorSnippet"]).strip()

            if len(prior) > 2000:
                prior = prior[:2000] + "…"

            lines.append(
                ChatTextContextVocabularyService.text(
                    "promptBlock",
                    "priorAssistant",
                    prior=prior,
                )
            )

        if context.get("referencesCanvas"):
            lines.append(
                ChatTextContextVocabularyService.text("promptBlock", "canvasSource")
            )

        if context.get("referencesAttachment"):
            lines.append(
                ChatTextContextVocabularyService.text("promptBlock", "attachmentSource")
            )

        if not lines:
            return None

        return "\n".join(lines)

    @classmethod
    def _extract_inline_text(cls, message: str) -> str | None:
        if not message.strip():
            return None

        verbs = "|".join(re.escape(verb) for verb in cls._inline_extract_verbs())

        colon_match = re.search(
            rf"(?:{verbs})\s*:\s*(.+)",
            message,
            re.IGNORECASE | re.DOTALL,
        )

        if colon_match:
            return colon_match.group(1).strip()

        below_match = re.search(
            r"(?:texto\s+ab(?:aixo|aixo)|abaixo)\s*:?\s*\n+([\s\S]+)",
            message,
            re.IGNORECASE,
        )

        if below_match:
            return below_match.group(1).strip()

        quoted = re.findall(r"«([^»]+)»|\"([^\"]+)\"|'([^']+)'", message)

        for groups in quoted:
            for value in groups:
                if value and len(value.strip()) > 12:
                    return value.strip()

        return None

    @classmethod
    def _latest_assistant_snippet(cls, previous_messages: list) -> str | None:
        for msg in reversed(previous_messages or []):
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)

            if role != "assistant":
                continue

            content = getattr(msg, "content", None) or (
                msg.get("content") if isinstance(msg, dict) else None
            )

            if isinstance(content, str) and content.strip():
                return content.strip()

        return None
