"""Delegate — intenção de consulta de produto."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

from app.domain.services.chat_product_query_intent.chat_product_query_intent_content_service import (
    ChatProductQueryIntentContentService,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_facade_access import (
    intent_service,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_models import (
    ChatProductQueryIntent,
)
from app.domain.services.chat_product_query_intent.chat_product_query_intent_vocabulary import (
    ChatProductQueryIntentVocabulary as VOCAB,
)

_INTENT_CONTENT_BUNDLE = "product_query_intent"



class ChatProductQueryIntentDirectAnswerService:
    @staticmethod
    def _humanized_lines(humanized: dict) -> list[str]:
        from app.domain.services.chat_presentation_prose_delivery_service import (
            ChatPresentationProseDeliveryService,
        )

        return ChatPresentationProseDeliveryService.resolve_humanized_lines_for_facts(
            {"humanizedSummary": humanized},
        )

    @classmethod
    def format_direct_answer(cls,
        humanized: dict,
        *,
        intent: str,
        path: str | None = None,
    ) -> str | None:
        normalized_path = str(path or "").lower()

        if intent in {
            ChatProductQueryIntent.MULTI_SCOPE,
            ChatProductQueryIntent.STOCK,
            ChatProductQueryIntent.PARENTS,
        } or (
            intent == ChatProductQueryIntent.FULL
            and ChatProductQueryIntentDirectAnswerService._is_product_operational_path(normalized_path)
        ):
            brief = ChatProductQueryIntentDirectAnswerService._format_product_scope_brief(
                humanized,
                intent=intent,
                path=normalized_path,
            )

            if brief:
                return brief

        if intent == ChatProductQueryIntent.STRUCTURE:
            from app.domain.services.chat_product_structure_presentation_service import (
                ChatProductStructurePresentationService,
            )

            dados = humanized.get("dados")

            if isinstance(dados, dict):
                formatted = ChatProductStructurePresentationService.format_markdown(
                    dados,
                    source_path=humanized.get("sourcePath"),
                )

                if formatted:
                    return formatted

        lines = ChatProductQueryIntentDirectAnswerService._humanized_lines(humanized)

        if not lines:
            return None

        title = str(humanized.get("titulo") or "").strip()

        if intent == ChatProductQueryIntent.DESCRIPTION:
            parts = [title] if title else []
            parts.append(lines[0])
            return "\n\n".join(parts)

        filtered = [line for line in lines if not VOCAB.ZERO_RECORDS_RE.search(line)]
        parts = [title] if title else []
        parts.extend(filtered or lines)
        return "\n\n".join(parts)

    @classmethod
    def _is_product_operational_path(cls, path: str) -> bool:
        return any(
            segment in path
            for segment in (
                "/stock",
                "/parents",
                "/guide",
                "/inspection",
                "/structure",
            )
        )

    @classmethod
    def _format_product_scope_brief(cls,
        humanized: dict,
        *,
        intent: str,
        path: str,
    ) -> str | None:
        lines = [
            str(line).strip()
            for line in ChatProductQueryIntentDirectAnswerService._humanized_lines(humanized)
            if str(line).strip() and not VOCAB.ZERO_RECORDS_RE.search(str(line).strip())
        ]

        if not lines:
            return None

        title = str(humanized.get("titulo") or "").strip()
        header = title or ChatProductQueryIntentContentService._header("default", default="Consulta do produto")
        body = "\n\n".join(lines[:3])

        if intent == ChatProductQueryIntent.STOCK or "/stock" in path:
            header = title or ChatProductQueryIntentContentService._header("stock", default="Estoque do produto")

        if intent == ChatProductQueryIntent.PARENTS or "/parents" in path:
            header = title or ChatProductQueryIntentContentService._header("parents", default="Onde o item é usado")

        return f"**{header}**\n\n{body}"

    @classmethod
    def _filter_stock_lines(cls, lines: list[str]) -> list[str]:
        stock_lines = []

        for line in lines:
            lowered = line.lower()

            if any(
                token in lowered
                for token in ChatProductQueryIntentContentService._terms("stock", "lineTokens")
            ):
                stock_lines.append(line)

        return stock_lines

