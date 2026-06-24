"""Desambiguação de escopo operacional com produto — exclusões declarativas."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_sub_intent_service import (
    ChatOperationalSubIntentService,
)
from app.domain.services.chat_product_query_intent_detection_service import (
    ChatProductQueryIntentDetectionService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_product_route_predicate_service import (
    ChatProductRoutePredicateService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
    ProductionOperationalIntentKind,
)


class ChatOperationalAmbiguityService:
    BUNDLE = "product_query_intent"
    ROUTER = "router"

    @classmethod
    def resolve(
        cls,
        message: str,
        resolved_params: dict[str, str] | None,
    ) -> tuple[bool, tuple[str, ...]]:
        code = (resolved_params or {}).get("productCode") or ChatProductQueryIntentService.extract_product_code(
            message
        )

        if not code:
            return False, ()

        lowered = message.lower()

        if (
            ChatProductionOperationalIntentService.resolve(message)
            == ProductionOperationalIntentKind.SCHEDULE_TODAY
        ):
            return False, ()

        sub_intent = ChatOperationalSubIntentService.resolve(message)

        if sub_intent and sub_intent != "product_lookup":
            return False, ()

        if sub_intent == "product_lookup" and any(
            term in lowered
            for term in cls._router_terms("operationalAmbiguityProductLookupExcludes")
        ):
            return False, ()

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if cls._matches_exclusion(message, normalized, lowered):
            return False, ()

        if (
            any(term in lowered for term in cls._scope_terms())
            or ChatOperationalSubIntentService._mentions_supplier(lowered)
            or ChatOperationalSubIntentService._mentions_outbound_invoice(lowered)
        ):
            return False, ()

        if "produto" not in lowered and code not in message:
            return False, ()

        return True, cls._candidates()

    @classmethod
    def _matches_exclusion(cls, message: str, normalized: str, lowered: str) -> bool:
        for predicate in cls._exclusion_predicates():
            if ChatProductRoutePredicateService.matches(
                predicate,
                normalized,
                message=message,
            ):
                return True

        for probe in cls._exclusion_probes():
            if probe == "fullAnalyserQuestion":
                if ChatProductQueryIntentDetectionService.looks_like_full_analyser_question(
                    message
                ):
                    return True

                continue

            if ChatOperationalSubIntentService._run_probe(
                probe,
                message,
                normalized,
                lowered,
            ):
                return True

        return False

    @classmethod
    def _exclusion_predicates(cls) -> tuple[str, ...]:
        return cls._router_string_list("operationalAmbiguityExclusionPredicates")

    @classmethod
    def _exclusion_probes(cls) -> tuple[str, ...]:
        return cls._router_string_list("operationalAmbiguityProbes")

    @classmethod
    def _candidates(cls) -> tuple[str, ...]:
        values = cls._router_string_list("operationalAmbiguityCandidates")

        if values:
            return values

        return (
            "product_lookup",
            "stock_lookup",
            "supplier_lookup",
            "structure_lookup",
            "sales_lookup",
            "purchase_lookup",
        )

    @classmethod
    def _scope_terms(cls) -> tuple[str, ...]:
        return tuple(
            ChatAssistantContentService.list(
                cls.BUNDLE,
                "operationalAmbiguityScopeTerms",
            )
        )

    @classmethod
    def _router_terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(cls.BUNDLE, cls.ROUTER, *path))

    @classmethod
    def _router_string_list(cls, key: str) -> tuple[str, ...]:
        node = ChatAssistantContentService.get_node(cls.BUNDLE, cls.ROUTER, key)

        if not isinstance(node, list):
            return ()

        return tuple(
            str(item).strip()
            for item in node
            if str(item or "").strip()
        )
