"""Guarda transversal de vazamento de instrução na prosa de síntese LLM."""

from __future__ import annotations

from collections.abc import Iterable

from app.domain.services.chat_llm_synthesis_delivery_content_service import (
    ChatLlmSynthesisDeliveryContentService,
)

_FACTS_TITLE_MIN_CHARS = 8


class ChatLlmSynthesisLeakGuardService:
    @classmethod
    def merge_markers(cls, *groups: Iterable[str]) -> tuple[str, ...]:
        seen: set[str] = set()
        ordered: list[str] = []

        for group in groups:
            for item in group or ():
                marker = str(item or "").strip().lower()
                if not marker or marker in seen:
                    continue
                seen.add(marker)
                ordered.append(marker)

        return tuple(ordered)

    @classmethod
    def collected_leak_markers(cls, *family_markers: Iterable[str]) -> tuple[str, ...]:
        return cls.merge_markers(
            ChatLlmSynthesisDeliveryContentService.common_leak_markers(),
            *family_markers,
        )

    @classmethod
    def needs_fallback(
        cls,
        *,
        answer: str,
        facts: str | None = None,
        leak_markers: Iterable[str] = (),
        placeholder_markers: Iterable[str] = (),
        required_substrings: Iterable[str] = (),
    ) -> bool:
        text = str(answer or "").strip()
        if not text:
            return True

        lowered = text.lower()
        markers = cls.collected_leak_markers(leak_markers)

        for marker in markers:
            if marker and marker in lowered:
                return True

        for marker in placeholder_markers or ():
            token = str(marker or "").strip().lower()
            if token and token in lowered:
                return True

        facts_block = str(facts or "").strip()
        facts_title = facts_block.splitlines()[0].strip().lower() if facts_block else ""
        if facts_title and len(facts_title) >= _FACTS_TITLE_MIN_CHARS and facts_title in lowered:
            return True

        required = [
            str(item).strip().lower()
            for item in (required_substrings or ())
            if str(item).strip()
        ]
        if required and not any(item in lowered for item in required):
            return True

        return False

    @classmethod
    def guard_answer(
        cls,
        *,
        answer: str,
        fallback: str | None,
        facts: str | None = None,
        leak_markers: Iterable[str] = (),
        placeholder_markers: Iterable[str] = (),
        required_substrings: Iterable[str] = (),
    ) -> str:
        text = str(answer or "").strip()
        recovery = str(fallback or "").strip()

        if not cls.needs_fallback(
            answer=text,
            facts=facts,
            leak_markers=leak_markers,
            placeholder_markers=placeholder_markers,
            required_substrings=required_substrings,
        ):
            return text

        if recovery:
            return recovery

        safe = ChatLlmSynthesisDeliveryContentService.safe_fallback_answer()
        if safe:
            return safe

        return text
