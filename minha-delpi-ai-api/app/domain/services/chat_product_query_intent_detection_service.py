"""Pipeline declarativo de detect/refine para intenção de produto (DOCIE)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatProductQueryIntentDetectionService:
    BUNDLE = "product_query_intent"

    @classmethod
    def detect(cls, message: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        for step in cls._detect_pipeline():
            intent = cls._evaluate_step(step, message, normalized)

            if intent:
                return intent

        return cls._default_intent()

    @classmethod
    def refine_operational_intent_from_full(
        cls,
        message: str,
        *,
        normalized: str | None = None,
    ) -> str:
        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message
        )

        for step in cls._refinement_pipeline():
            intent = cls._evaluate_step(step, message, normalized_text)

            if intent:
                return intent

        return "full"

    @classmethod
    def looks_like_mixed_documental_operational(cls, normalized: str) -> bool:
        return cls._message_has_any_marker(
            normalized,
            "mixedDocumental",
            "documental",
        ) and cls._message_has_any_marker(
            normalized,
            "mixedDocumental",
            "operational",
        )

    @classmethod
    def looks_like_explicit_playbook_product_scope(cls, normalized: str) -> bool:
        from app.domain.services.operational_route_registry_service import (
            OperationalRouteRegistryService,
        )

        return cls._matches_any_predicates(
            OperationalRouteRegistryService.playbook_product_predicates(),
            normalized,
        )

    @classmethod
    def looks_like_generic_product_analysis_question(cls, normalized: str) -> bool:
        if "produt" not in normalized:
            return False

        if not re.search(r"\banalis", normalized):
            return False

        if cls._message_has_any_marker(normalized, "analyser", "genericAnalysisExclude"):
            return False

        if cls._message_has_any_marker(normalized, "operationalAmbiguityScopeTerms"):
            return False

        return True

    @classmethod
    def looks_like_full_analyser_question(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if cls._message_has_any_marker(normalized, "analyser", "fullQuestion"):
            return True

        if cls.looks_like_generic_product_analysis_question(normalized):
            return True

        from app.domain.services.chat_product_multi_scope_planning_service import (
            ChatProductMultiScopePlanningService,
        )

        scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(message)

        return ChatProductMultiScopePlanningService.should_use_single_analyser(
            scopes,
            message,
        )

    @classmethod
    def looks_like_product_summary_question(cls, normalized: str) -> bool:
        if cls._message_has_any_marker(normalized, "analyser", "summaryExclude"):
            return False

        if cls._message_has_any_marker(normalized, "analyser", "summaryExplicit"):
            return True

        if "resumo" not in normalized:
            return False

        if cls._message_has_any_marker(normalized, "analyser", "summaryExcludeWhenResumo"):
            return False

        from app.domain.services.chat_product_plural_phrasing_service import (
            ChatProductPluralPhrasingService,
        )

        return ChatProductPluralPhrasingService.has_product_entity_reference(normalized)

    @classmethod
    def _detect_pipeline(cls) -> list[dict[str, Any]]:
        return cls._pipeline("intentDetectPipeline")

    @classmethod
    def _refinement_pipeline(cls) -> list[dict[str, Any]]:
        return cls._pipeline("intentRefinementPipeline")

    @classmethod
    def _pipeline(cls, key: str) -> list[dict[str, Any]]:
        node = ChatAssistantContentService.get_node(cls.BUNDLE, key) or []

        if not isinstance(node, list):
            return []

        return [item for item in node if isinstance(item, dict)]

    @classmethod
    def _default_intent(cls) -> str:
        token = str(
            ChatAssistantContentService.get(cls.BUNDLE, "intentDetectDefault") or "full"
        ).strip()

        return token or "full"

    @classmethod
    def _evaluate_step(
        cls,
        step: dict[str, Any],
        message: str,
        normalized: str,
    ) -> str | None:
        probe = str(step.get("probe") or "").strip()

        if probe == "singleScopeIntent":
            return cls._single_scope_intent(message)

        if not cls._step_matches(step, message, normalized):
            return None

        intent = str(step.get("intent") or "").strip()

        return intent or None

    @classmethod
    def _step_matches(cls, step: dict[str, Any], message: str, normalized: str) -> bool:
        predicate = str(step.get("predicate") or "").strip()

        if predicate:
            from app.domain.services.chat_product_route_predicate_service import (
                ChatProductRoutePredicateService,
            )

            return ChatProductRoutePredicateService.matches(
                predicate,
                normalized,
                message=message,
            )

        probe = str(step.get("probe") or "").strip()

        if probe:
            return cls._run_probe(probe, message, normalized)

        return False

    @classmethod
    def _run_probe(cls, probe: str, message: str, normalized: str) -> bool:
        if probe == "drawingAnalysis":
            from app.domain.services.chat_drawing_intent_service import (
                ChatDrawingIntentService,
            )

            return ChatDrawingIntentService.is_drawing_analysis_request(message)

        if probe == "mixedDocumentalOperational":
            return cls.looks_like_mixed_documental_operational(normalized)

        if probe == "explicitPlaybookProductScope":
            return cls.looks_like_explicit_playbook_product_scope(normalized)

        if probe == "multiScopeSingleAnalyser":
            return cls._matches_multi_scope_single_analyser(message)

        if probe == "multiScope":
            return cls._matches_multi_scope(message)

        if probe == "fullAnalyserQuestion":
            return cls.looks_like_full_analyser_question(message)

        if probe == "productSummaryQuestion":
            return cls.looks_like_product_summary_question(normalized)

        if probe == "productOverviewMessage":
            from app.domain.services.chat_product_overview_intent_service import (
                ChatProductOverviewIntentService,
            )

            return ChatProductOverviewIntentService.is_product_overview_message(message)

        if probe == "singleScopeIntent":
            return cls._single_scope_intent(message) is not None

        return False

    @classmethod
    def _matches_multi_scope_single_analyser(cls, message: str) -> bool:
        from app.domain.services.chat_product_multi_scope_planning_service import (
            ChatProductMultiScopePlanningService,
        )

        scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(message)

        if len(scopes) < 2:
            return False

        return ChatProductMultiScopePlanningService.should_use_single_analyser(
            scopes,
            message,
        )

    @classmethod
    def _matches_multi_scope(cls, message: str) -> bool:
        from app.domain.services.chat_product_multi_scope_planning_service import (
            ChatProductMultiScopePlanningService,
        )

        scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(message)

        return len(scopes) >= 2

    @classmethod
    def _single_scope_intent(cls, message: str) -> str | None:
        from app.domain.services.chat_product_multi_scope_planning_service import (
            ChatProductMultiScopePlanningService,
        )

        scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(message)

        if len(scopes) != 1:
            return None

        mapping = ChatAssistantContentService.get_node(cls.BUNDLE, "singleScopeIntentMap") or {}

        if not isinstance(mapping, dict):
            return None

        mapped = mapping.get(scopes[0])

        return str(mapped).strip() if mapped else None

    @classmethod
    def _terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(cls.BUNDLE, *path))

    @classmethod
    def _message_has_any_marker(cls, normalized: str, *path: str) -> bool:
        return any(term in normalized for term in cls._terms(*path))

    @classmethod
    def _matches_any_predicates(
        cls,
        predicates: list[str] | tuple[str, ...],
        normalized: str,
    ) -> bool:
        from app.domain.services.operational_route_matcher_service import (
            OperationalRouteMatcherService,
        )

        return any(
            OperationalRouteMatcherService.matches_custom_predicate(predicate, normalized)
            for predicate in predicates
        )
