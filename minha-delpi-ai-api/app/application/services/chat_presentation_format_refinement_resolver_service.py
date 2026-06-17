"""Resolve refinamento de formato: vocabulário → heurísticas → LLM → resposta honesta."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.application.services.chat_turn.chat_turn_preparation_content_service import (
    ChatTurnPreparationContentService,
)
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.chat_presentation_format_refinement_intent_service import (
    ChatPresentationFormatRefinementIntentService,
    FormatRefinementIntent,
)
from app.domain.services.chat_presentation_format_refinement_service import (
    ChatPresentationFormatRefinementService,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService

logger = logging.getLogger("minha-delpi-ai-api.presentation.format_refinement")


class ChatPresentationFormatRefinementResolverService:
    _ALLOWED_LLM_FORMATS = frozenset(
        {"chart", "table", "text", "tree", "dashboard", "canvas", "kpi", "none"}
    )

    def __init__(self, llm_gateway: LlmGatewayPort | None = None):
        self._llm_gateway = llm_gateway

    def resolve(
        self,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
    ) -> FormatRefinementIntent:
        has_prior = (
            ChatPresentationFormatRefinementService.collect_last_successful_operation(
                previous_messages,
            )
            is not None
        )

        intent = ChatPresentationFormatRefinementIntentService.resolve(
            message,
            has_prior_operation=has_prior,
        )

        if not intent.is_refinement:
            return intent

        if intent.requested_format:
            return intent

        llm_format = self._resolve_with_llm(message, has_prior_operation=has_prior)

        if llm_format and llm_format != "none":
            return FormatRefinementIntent(
                is_refinement=True,
                requested_format=llm_format,
                source="llm",
                confidence=0.68,
            )

        if self._should_defer_to_web_search(message):
            return FormatRefinementIntent(is_refinement=False)

        if intent.is_refinement:
            return intent

        return FormatRefinementIntent(is_refinement=False)

    def build_failure_direct_answer(
        self,
        message: str | None,
        *,
        previous_messages: list[Any] | None = None,
        requested_format: str | None = None,
        reason: str = "unrecognized",
    ) -> str | None:
        operation = ChatPresentationFormatRefinementService.collect_last_successful_operation(
            previous_messages,
        )

        if not operation:
            return ChatTurnPreparationContentService.get(
                "directAnswers",
                "formatRefinement",
                "noPriorResult",
            )

        if reason == "chart_build_failed":
            return ChatTurnPreparationContentService.get(
                "directAnswers",
                "formatRefinement",
                "chartBuildFailed",
            )

        if reason == "unsupported_format" and requested_format:
            return ChatTurnPreparationContentService.format(
                "directAnswers",
                "formatRefinement",
                "unsupportedFormat",
                format=requested_format,
            )

        return ChatTurnPreparationContentService.get(
            "directAnswers",
            "formatRefinement",
            "unrecognizedFormat",
        )

    def _resolve_with_llm(
        self,
        message: str | None,
        *,
        has_prior_operation: bool,
    ) -> str | None:
        if not self._llm_gateway or not has_prior_operation:
            return None

        prompt = ChatTurnPreparationContentService.get(
            "directAnswers",
            "formatRefinement",
            "llmSystemPrompt",
        )
        normalized = str(message or "").strip()[:800]

        if not normalized:
            return None

        try:
            raw = self._llm_gateway.generate(
                [
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": (
                            "Mensagem do usuário pedindo mudança de visualização "
                            f"do último resultado:\n{normalized}"
                        ),
                    },
                ]
            )
        except Exception as exc:
            logger.warning("Format refinement LLM skipped: %s", exc)
            return None

        return self._parse_llm_format(raw)

    @classmethod
    def _parse_llm_format(cls, raw: str) -> str | None:
        payload = cls._extract_json(raw)

        if not isinstance(payload, dict):
            return None

        token = str(payload.get("format") or payload.get("requestedFormat") or "").strip().lower()

        if token in cls._ALLOWED_LLM_FORMATS:
            return None if token == "none" else token

        return None

    @staticmethod
    def _extract_json(raw: str) -> object | None:
        text = str(raw or "").strip()

        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]*\}", text)

            if not match:
                return None

            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None

    @staticmethod
    def _should_defer_to_web_search(message: str | None) -> bool:
        normalized = str(message or "").strip()

        if not normalized:
            return False

        return ChatWebSearchIntentService.is_explicit_request(normalized)
