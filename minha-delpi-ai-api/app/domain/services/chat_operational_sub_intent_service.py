"""Sub-intenção operacional do router — pipeline declarativo em product_query_intent.json."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_route_predicate_service import (
    ChatProductRoutePredicateService,
)


class ChatOperationalSubIntentService:
    BUNDLE = "product_query_intent"
    ROUTER = "router"

    @classmethod
    def resolve(cls, message: str) -> str | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        lowered = message.lower()

        for step in cls._pipeline():
            sub_intent = cls._evaluate_step(step, message, normalized, lowered)

            if sub_intent:
                return sub_intent

        return None

    @classmethod
    def _pipeline(cls) -> list[dict[str, Any]]:
        node = ChatAssistantContentService.get_node(
            cls.BUNDLE,
            cls.ROUTER,
            "operationalSubIntentPipeline",
        )

        if not isinstance(node, list):
            return []

        return [item for item in node if isinstance(item, dict)]

    @classmethod
    def _evaluate_step(
        cls,
        step: dict[str, Any],
        message: str,
        normalized: str,
        lowered: str,
    ) -> str | None:
        if not cls._step_matches(step, message, normalized, lowered):
            return None

        sub_intent = str(step.get("subIntent") or "").strip()

        return sub_intent or None

    @classmethod
    def _step_matches(
        cls,
        step: dict[str, Any],
        message: str,
        normalized: str,
        lowered: str,
    ) -> bool:
        probe = str(step.get("probe") or "").strip()

        if probe:
            return cls._run_probe(probe, message, normalized, lowered)

        predicate = str(step.get("predicate") or "").strip()

        if predicate:
            return ChatProductRoutePredicateService.matches(
                predicate,
                normalized,
                message=message,
            )

        terms_key = str(step.get("termsAny") or "").strip()

        if terms_key:
            return any(term in lowered for term in cls._router_terms(terms_key))

        message_contains = str(step.get("messageContains") or "").strip().lower()

        if message_contains:
            return message_contains in lowered

        return False

    @classmethod
    def _run_probe(
        cls,
        probe: str,
        message: str,
        normalized: str,
        lowered: str,
    ) -> bool:
        handler = cls._probe_handlers().get(probe)

        if handler is None:
            return False

        return bool(handler(message, normalized, lowered))

    @classmethod
    def _probe_handlers(cls):
        from app.domain.services.chat_product_query_intent_detection_service import (
            ChatProductQueryIntentDetectionService,
        )
        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
            ProductionOperationalIntentKind,
        )

        return {
            "productionScheduleToday": lambda message, _normalized, _lowered: (
                ChatProductionOperationalIntentService.resolve(message)
                == ProductionOperationalIntentKind.SCHEDULE_TODAY
            ),
            "outboundInvoice": lambda _message, _normalized, lowered: (
                cls._mentions_outbound_invoice(lowered)
            ),
            "supplierMention": lambda _message, _normalized, lowered: (
                cls._mentions_supplier(lowered)
            ),
            "fullAnalyserQuestion": lambda message, _normalized, _lowered: (
                ChatProductQueryIntentDetectionService.looks_like_full_analyser_question(
                    message
                )
            ),
            "systemMetadataQuestion": lambda _message, _normalized, lowered: (
                any(
                    term in lowered
                    for term in cls._router_terms("systemMetadataTableTerms")
                )
                and any(
                    phrase in lowered
                    for phrase in cls._router_terms("systemMetadataQuestionPhrases")
                )
            ),
        }

    @classmethod
    def _router_terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(cls.BUNDLE, cls.ROUTER, *path))

    @classmethod
    def _mentions_supplier(cls, lowered: str) -> bool:
        if any(term in lowered for term in cls._router_terms("supplierMentionTerms")):
            return True

        return bool(re.search(r"\bfornece", lowered))

    @classmethod
    def _mentions_outbound_invoice(cls, lowered: str) -> bool:
        if any(
            term in lowered
            for term in cls._router_terms("invoiceOutbound", "inboundExcludePhrases")
        ):
            return False

        if any(
            term in lowered
            for term in cls._router_terms("invoiceOutbound", "outboundPhrases")
        ):
            return True

        if "notas fiscais" in lowered and (
            "saída" in lowered or "saida" in lowered or "venda" in lowered
        ):
            return True

        return bool(re.search(r"\bnf(?:e)?\b", lowered)) and (
            "saída" in lowered or "saida" in lowered
        )
