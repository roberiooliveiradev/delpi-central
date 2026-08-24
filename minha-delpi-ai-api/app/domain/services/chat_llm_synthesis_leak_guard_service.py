"""Guarda transversal de vazamento de instrução na prosa de síntese LLM."""

from __future__ import annotations

import re
from collections.abc import Iterable

from app.domain.services.chat_llm_synthesis_delivery_content_service import (
    ChatLlmSynthesisDeliveryContentService,
)

_FACTS_TITLE_MIN_CHARS = 8
_WHITESPACE_RE = re.compile(r"\s+")


class ChatLlmSynthesisLeakGuardService:
    @classmethod
    def compact_for_match(cls, value: str) -> str:
        """Remove espaços — Kimi/OpenRouter às vezes colapsa espaços no CoT."""
        return _WHITESPACE_RE.sub("", str(value or "").lower())

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
    def _contains_marker(cls, *, haystack: str, haystack_compact: str, marker: str) -> bool:
        token = str(marker or "").strip().lower()
        if not token:
            return False
        if token in haystack:
            return True
        compact_marker = cls.compact_for_match(token)
        return bool(compact_marker) and compact_marker in haystack_compact

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
        compact = cls.compact_for_match(text)
        markers = cls.collected_leak_markers(leak_markers)

        for marker in markers:
            if cls._contains_marker(
                haystack=lowered, haystack_compact=compact, marker=marker
            ):
                return True

        for marker in placeholder_markers or ():
            if cls._contains_marker(
                haystack=lowered, haystack_compact=compact, marker=str(marker)
            ):
                return True

        facts_block = str(facts or "").strip()
        facts_title = facts_block.splitlines()[0].strip().lower() if facts_block else ""
        if facts_title and len(facts_title) >= _FACTS_TITLE_MIN_CHARS:
            if facts_title in lowered or cls.compact_for_match(facts_title) in compact:
                return True

        required = [
            str(item).strip().lower()
            for item in (required_substrings or ())
            if str(item).strip()
        ]
        if required and not any(
            item in lowered or cls.compact_for_match(item) in compact for item in required
        ):
            return True

        if cls.looks_like_english_answer(text):
            return True

        return False

    @classmethod
    def looks_like_english_answer(cls, answer: str) -> bool:
        """Heurística declarativa: resposta predominantemente EN sem acentos PT."""
        text = str(answer or "").strip()
        if len(text) < 40:
            return False

        if re.search(r"[áàâãéêíóôõúç]", text, re.IGNORECASE):
            return False

        lowered = text.lower()
        compact = cls.compact_for_match(text)
        markers = ChatLlmSynthesisDeliveryContentService.english_answer_markers()
        min_hits = ChatLlmSynthesisDeliveryContentService.english_answer_min_marker_hits()

        hits = 0
        for marker in markers:
            token = str(marker or "").strip().lower()
            if not token:
                continue
            if cls._contains_marker(
                haystack=lowered, haystack_compact=compact, marker=token
            ):
                hits += 1

        return hits >= max(1, min_hits)

    @classmethod
    def try_recover_portuguese_body(cls, answer: str) -> str | None:
        """Se CoT EN vier antes da prosa PT, mantém só o corpo em português."""
        text = str(answer or "")
        if not text.strip():
            return None

        starts = ChatLlmSynthesisDeliveryContentService.portuguese_body_start_markers()
        best_idx: int | None = None

        for marker in starts:
            idx = text.find(marker)
            if idx <= 0:
                continue
            if best_idx is None or idx < best_idx:
                best_idx = idx

        if best_idx is None:
            return None

        prefix = text[:best_idx]
        body = text[best_idx:].strip()
        if not body or len(body) < 40:
            return None

        if not cls.needs_fallback(answer=prefix):
            # Prefixo sem leak conhecido — não cortar resposta legítima.
            return None

        if cls.needs_fallback(answer=body):
            return None

        return body

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

        recovered = cls.try_recover_portuguese_body(text)
        if recovered:
            return recovered

        if recovery:
            return recovery

        safe = ChatLlmSynthesisDeliveryContentService.safe_fallback_answer()
        if safe:
            return safe

        return text
