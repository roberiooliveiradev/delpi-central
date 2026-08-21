"""Vocabulário declarativo de capacidades — bundle ``capabilities``."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "capabilities"


class ChatCapabilitiesContentService:
    @classmethod
    def llm_synthesis_user_message_lead(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "llmSynthesis",
                "userMessageLead",
                default="",
            )
            or ""
        ).strip()

    @classmethod
    def llm_synthesis_question_prefix(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "llmSynthesis",
                "userMessageQuestionPrefix",
                default="Pergunta:",
            )
            or "Pergunta:"
        ).strip()

    @classmethod
    def llm_synthesis_facts_section_title(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "llmSynthesis",
                "factsSectionTitle",
                default="O que você pode fazer aqui",
            )
            or "O que você pode fazer aqui"
        ).strip()

    @classmethod
    def llm_synthesis_compound_section_title(cls) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "llmSynthesis",
                "compoundSectionTitle",
                default="O que você pode fazer aqui",
            )
            or "O que você pode fazer aqui"
        ).strip()

    @classmethod
    def leak_markers(cls) -> tuple[str, ...]:
        return tuple(
            str(item).strip().lower()
            for item in ChatAssistantContentService.list(
                _BUNDLE, "llmSynthesis", "leakMarkers"
            )
            if str(item).strip()
        )

    @classmethod
    def facts_max_chars_for_mode(cls, response_mode: str | None) -> int | None:
        mode = str(response_mode or "normal").strip().lower() or "normal"
        if mode not in {"fast", "normal", "thinker"}:
            mode = "normal"
        node = ChatAssistantContentService.get_node(
            _BUNDLE,
            "llmSynthesis",
            "factsMaxCharsByMode",
        )
        if not isinstance(node, dict):
            return None
        raw = node.get(mode)
        if raw in (None, ""):
            return None
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return None
        if value <= 0:
            return None
        return value

    @classmethod
    def clip_facts_for_mode(cls, facts: str, response_mode: str | None) -> str:
        text = str(facts or "").strip()
        if not text:
            return ""
        max_chars = cls.facts_max_chars_for_mode(response_mode)
        if max_chars is None or len(text) <= max_chars:
            return text
        lines = text.splitlines()
        if not lines:
            return text[:max_chars].rstrip()
        kept = [lines[0]]
        size = len(lines[0])
        for line in lines[1:]:
            candidate = size + 1 + len(line)
            if candidate > max_chars:
                break
            kept.append(line)
            size = candidate
        clipped = "\n".join(kept).strip()
        return clipped or text[:max_chars].rstrip()
