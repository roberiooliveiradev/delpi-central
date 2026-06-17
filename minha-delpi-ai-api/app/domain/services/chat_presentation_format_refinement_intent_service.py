"""Detecção em camadas de refinamento de formato (tabela/gráfico/texto/árvore)."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_presentation_format_vocabulary_service import (
    ChatPresentationFormatVocabularyService,
)


@dataclass(frozen=True)
class FormatRefinementIntent:
    is_refinement: bool
    requested_format: str | None = None
    source: str = "none"
    confidence: float = 0.0


class ChatPresentationFormatRefinementIntentService:
    _ALLOWED_FORMATS = frozenset(
        {"text", "table", "tree", "chart", "dashboard", "canvas", "kpi"}
    )

    @classmethod
    def resolve(
        cls,
        message: str | None,
        *,
        has_prior_operation: bool = False,
    ) -> FormatRefinementIntent:
        lowered = str(message or "").strip().lower()

        if not lowered:
            return FormatRefinementIntent(is_refinement=False)

        requested = cls.detect_requested_format(lowered)

        if requested and cls.looks_like_format_refinement(lowered, requested_format=requested):
            return FormatRefinementIntent(
                is_refinement=True,
                requested_format=requested,
                source="vocabulary",
                confidence=0.92,
            )

        if has_prior_operation:
            loose = cls._detect_from_loose_keywords(lowered)

            if loose and cls._has_refinement_context(lowered):
                return FormatRefinementIntent(
                    is_refinement=True,
                    requested_format=loose,
                    source="loose",
                    confidence=0.78,
                )

            router_format = cls._detect_from_router_terms(lowered)

            if router_format and cls._has_refinement_context(lowered):
                return FormatRefinementIntent(
                    is_refinement=True,
                    requested_format=router_format,
                    source="router",
                    confidence=0.72,
                )

            normalized = ChatMessageNormalizationService.normalize_for_matching(
                message or "",
            ).lower()

            if normalized != lowered:
                retry = cls.detect_requested_format(normalized)

                if retry and cls.looks_like_format_refinement(
                    normalized,
                    requested_format=retry,
                ):
                    return FormatRefinementIntent(
                        is_refinement=True,
                        requested_format=retry,
                        source="normalization",
                        confidence=0.85,
                    )

        if cls._might_be_ambiguous_refinement(lowered, has_prior_operation=has_prior_operation):
            return FormatRefinementIntent(
                is_refinement=True,
                requested_format=None,
                source="ambiguous",
                confidence=0.45,
            )

        return FormatRefinementIntent(is_refinement=False)

    @classmethod
    def looks_like_format_refinement(
        cls,
        message: str | None,
        *,
        requested_format: str | None = None,
    ) -> bool:
        lowered = str(message or "").strip().lower()

        if not lowered:
            return False

        has_format = bool(requested_format or cls.detect_requested_format(lowered))

        if not has_format:
            return False

        if any(
            token in lowered
            for token in ChatPresentationFormatVocabularyService.reference_hints()
        ):
            return True

        if any(
            token in lowered
            for token in ChatPresentationFormatVocabularyService.last_result_terms()
        ):
            return True

        if cls._has_imperative_format_intent(lowered):
            return True

        if cls._has_refinement_context(lowered):
            return True

        return False

    @classmethod
    def detect_requested_format(cls, message: str) -> str | None:
        lowered = str(message or "").lower()

        if cls._matches_negative_format(lowered):
            return "text"

        for fmt in ("text", "tree", "table", "dashboard", "canvas", "kpi", "chart"):
            if cls._matches_format_hints(lowered, fmt):
                return fmt

        return None

    @classmethod
    def _matches_format_hints(cls, lowered: str, fmt: str) -> bool:
        if fmt == "text":
            return any(
                h in lowered
                for h in ChatPresentationFormatVocabularyService.text_hints(
                    include_tool_context=True,
                )
            )

        if fmt == "tree":
            return any(
                h in lowered
                for h in ChatPresentationFormatVocabularyService.tree_hints(
                    include_tool_context=True,
                )
            )

        if fmt == "table":
            return any(
                h in lowered
                for h in ChatPresentationFormatVocabularyService.table_hints(
                    include_tool_context=True,
                )
            )

        if fmt == "chart":
            return any(h in lowered for h in ChatPresentationFormatVocabularyService.chart_hints())

        if fmt == "dashboard":
            return any(
                h in lowered for h in ChatPresentationFormatVocabularyService.dashboard_hints()
            )

        if fmt == "canvas":
            return any(
                h in lowered for h in ChatPresentationFormatVocabularyService.canvas_hints()
            )

        if fmt == "kpi":
            return any(h in lowered for h in ChatPresentationFormatVocabularyService.kpi_hints())

        return False

    @classmethod
    def _matches_negative_format(cls, lowered: str) -> bool:
        return any(
            token in lowered for token in ChatPresentationFormatVocabularyService.negative_hints()
        ) and any(
            h in lowered
            for h in ChatPresentationFormatVocabularyService.text_hints(include_tool_context=True)
        )

    @classmethod
    def _has_imperative_format_intent(cls, lowered: str) -> bool:
        if not any(
            verb in lowered for verb in ChatPresentationFormatVocabularyService.imperative_verbs()
        ):
            return False

        return any(
            cls._matches_format_hints(lowered, fmt) for fmt in cls._ALLOWED_FORMATS
        )

    @classmethod
    def _has_refinement_context(cls, lowered: str) -> bool:
        return any(
            token in lowered for token in ChatPresentationFormatVocabularyService.reference_hints()
        ) or any(
            token in lowered
            for token in ChatPresentationFormatVocabularyService.last_result_terms()
        ) or any(
            token in lowered
            for token in ChatPresentationFormatVocabularyService.context_terms()
        )

    @classmethod
    def _detect_from_loose_keywords(cls, lowered: str) -> str | None:
        for fmt in ("chart", "table", "tree", "text", "dashboard", "canvas", "kpi"):
            for token in ChatPresentationFormatVocabularyService.loose_keywords(fmt):
                if token and token in lowered:
                    return fmt

        return None

    @classmethod
    def _detect_from_router_terms(cls, lowered: str) -> str | None:
        from app.domain.services.chat_intent_router_service import ChatIntentRouterService

        if not any(
            term in lowered
            for term in ChatIntentRouterService._intent_router_terms("presentationTerms")
        ):
            return None

        sub = ChatIntentRouterService._presentation_sub_intent(lowered)

        if sub in cls._ALLOWED_FORMATS:
            return sub

        if sub == "presentation":
            return cls._detect_from_loose_keywords(lowered)

        return None

    @classmethod
    def _might_be_ambiguous_refinement(
        cls,
        lowered: str,
        *,
        has_prior_operation: bool,
    ) -> bool:
        if not has_prior_operation:
            return False

        if any(
            token in lowered
            for token in ChatPresentationFormatVocabularyService.ambiguous_phrases()
        ):
            return True

        has_change_verb = any(
            verb in lowered for verb in ChatPresentationFormatVocabularyService.imperative_verbs()
        )
        has_visual_noun = bool(cls._detect_from_loose_keywords(lowered))

        return has_change_verb and has_visual_noun and not cls.detect_requested_format(lowered)
