"""Delegate — especialista SQL avançado."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_sql_intent_vocabulary_service import ChatSqlIntentVocabularyService
from app.domain.services.chat_sql_performance_advisor_service import ChatSqlPerformanceAdvisorService

from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_prompt_service import (
    ChatAdvancedSqlSpecialistPromptService,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_constants import (
    SQL_BLOCK_RE as _SQL_BLOCK_RE,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_facade_access import (
    sql_specialist_service,
)
from app.domain.services.chat_advanced_sql_specialist.chat_advanced_sql_specialist_types import (
    SqlSpecialistMode,
    _interactivity_content,
)



class ChatAdvancedSqlSpecialistProseFormattingService:
    @classmethod
    def _sql_authoring_intro(cls) -> str:
        return ChatSqlIntentVocabularyService.text(
            "advancedSqlSpecialist",
            "sqlAuthoringIntro",
        )

    @classmethod
    @lru_cache(maxsize=1)
    def _sql_authoring_intro_re(cls) -> re.Pattern[str]:
        intro = cls._sql_authoring_intro()
        prefix = re.escape(intro.split("(")[0].strip())

        return re.compile(
            rf"{prefix}\s*\([\s\S]*?conforme o ambiente:\s*",
            flags=re.IGNORECASE,
        )

    @classmethod
    def _normalize_prose_chunk(cls, value: str) -> str:
        cleaned = re.sub(r"```[\w]*", "", value, flags=re.IGNORECASE)
        cleaned = re.sub(r"`+", "", cleaned)

        return re.sub(r"\s+", " ", cleaned).strip().lower()

    @classmethod
    def _prose_chunks_similar(cls, left: str, right: str) -> bool:
        left_key = cls._normalize_prose_chunk(left)
        right_key = cls._normalize_prose_chunk(right)

        if not left_key or not right_key:
            return False

        if len(left_key) < 24 or len(right_key) < 24:
            return left_key == right_key

        if left_key in right_key or right_key in left_key:
            return True

        return (
            SequenceMatcher(None, left_key[:500], right_key[:500]).ratio() >= 0.82
        )

    @classmethod
    def _strip_redundant_sql_tail_prose(cls, text: str) -> str:
        blocks = list(_SQL_BLOCK_RE.finditer(text))

        if not blocks:
            return text

        primary = blocks[0]
        before = text[: primary.start()].strip()
        tail = _SQL_BLOCK_RE.sub("", text[primary.end() :]).strip()

        if not tail:
            return text[: primary.end()].strip()

        if before and cls._prose_chunks_similar(before, tail):
            return text[: primary.end()].strip()

        paragraphs = [part.strip() for part in re.split(r"\n\s*\n", tail) if part.strip()]
        kept: list[str] = []

        for paragraph in paragraphs:
            if before and cls._prose_chunks_similar(before, paragraph):
                continue

            if kept and cls._prose_chunks_similar(kept[-1], paragraph):
                continue

            kept.append(paragraph)

        if not kept:
            return text[: primary.end()].strip()

        return f"{text[: primary.end()].strip()}\n\n" + "\n\n".join(kept)

    @classmethod
    def _dedupe_sql_authoring_prose(cls, text: str) -> str:
        matches = list(cls._sql_authoring_intro_re().finditer(text))

        if len(matches) <= 1:
            return text.strip()

        first = matches[0]

        def _replace(match: re.Match[str]) -> str:
            if match.start() == first.start():
                return match.group(0)

            return ""

        cleaned = cls._sql_authoring_intro_re().sub(_replace, text)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()

    @classmethod
    def _extract_sql_from_fence(cls, fence: str) -> str:
        inner = re.sub(r"^```sql\s*", "", fence, flags=re.IGNORECASE)
        inner = re.sub(r"\s*```\s*$", "", inner)

        return inner.strip()

    @classmethod
    def _collect_unique_authoring_prose(cls, text: str) -> list[str]:
        fragments: list[str] = []
        cursor = 0

        for match in _SQL_BLOCK_RE.finditer(text):
            fragments.append(text[cursor : match.start()])
            cursor = match.end()

        fragments.append(text[cursor:])

        paragraphs: list[str] = []

        for fragment in fragments:
            scratch = cls._sql_authoring_intro_re().sub("\n", fragment)
            paragraphs.extend(
                part.strip() for part in re.split(r"\n\s*\n", scratch) if part.strip()
            )

        kept: list[str] = []

        for paragraph in paragraphs:
            if cls._prose_chunks_similar(cls._sql_authoring_intro(), paragraph):
                continue

            if kept and cls._prose_chunks_similar(kept[-1], paragraph):
                continue

            kept.append(paragraph)

        return kept

    @classmethod
    def _canonicalize_sql_authoring_layout(cls, text: str) -> str:
        blocks = re.findall(r"```sql\s*[\s\S]*?```", text, flags=re.IGNORECASE)

        if not blocks:
            return text.strip()

        sql_body = max(
            (cls._extract_sql_from_fence(block) for block in blocks),
            key=lambda body: (body.count("\n"), len(body)),
        )

        if not sql_body:
            return text.strip()

        before_first = re.split(r"```sql", text, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        custom_before = cls._sql_authoring_intro_re().sub("", before_first).strip()
        paragraphs = cls._collect_unique_authoring_prose(text)

        parts: list[str] = []

        if custom_before and len(custom_before) >= 16:
            parts.append(custom_before)
        else:
            parts.append(cls._sql_authoring_intro())

        parts.append(f"```sql\n{sql_body}\n```")

        for paragraph in paragraphs:
            if parts and cls._prose_chunks_similar(parts[0], paragraph):
                continue

            parts.append(paragraph)

        return "\n\n".join(parts).strip()

    @classmethod
    def format_sql_authoring_answer(cls, answer: str | None) -> str:
        text = str(answer or "").strip()

        if not text or "```sql" not in text.lower():
            return text

        text = cls._canonicalize_sql_authoring_layout(text)

        return cls._strip_redundant_sql_tail_prose(cls._dedupe_sql_authoring_prose(text))

    @classmethod
    def normalize_protheus_sql_answer(
        cls,
        answer: str | None,
        *,
        message: str | None = None,
        tool_calls: list | None = None,
    ) -> str:
        text = str(answer or "").strip()

        if not text or not sql_specialist_service().should_activate(message):
            return cls.format_sql_authoring_answer(text)

        sql_block = ChatSqlPerformanceAdvisorService.extract_sql_block(text)

        if not sql_block:
            return text

        columns = ChatAdvancedSqlSpecialistPromptService._column_hints_from_prefetch(tool_calls)
        sql_lower = sql_block.lower()
        uses_generic = any(
            token in sql_lower
            for token in (
                "codigocliente",
                "nomecliente",
                "codigo cliente",
                "nome cliente",
                "status = 'ativo'",
                "status='ativo'",
            )
        )
        uses_protheus = any(col.lower() in sql_lower for col in columns)
        domain_mismatch = ChatAdvancedSqlSpecialistPromptService._authoring_sql_domain_mismatch(
            message=message,
            sql_block=sql_block,
        )

        if not uses_generic and uses_protheus and not domain_mismatch:
            return text

        if domain_mismatch or uses_generic or not uses_protheus:
            replacement = ChatAdvancedSqlSpecialistPromptService._authoring_sql_from_message(
                message, columns
            )

            if not replacement:
                return text

            if "```sql" in text.lower():
                text = re.sub(
                    r"```sql\s*[\s\S]*?```",
                    f"```sql\n{replacement}\n```",
                    text,
                    count=1,
                    flags=re.IGNORECASE,
                )
            else:
                text = f"```sql\n{replacement}\n```\n\n{text}".strip()

            return cls.format_sql_authoring_answer(text)

        return text

