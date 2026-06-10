from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_sql_intent_vocabulary_service import (
    ChatSqlIntentVocabularyService,
)


class ChatSqlIntentService:
    """Diferencia elaborar/mostrar SQL de executar via action."""

    @classmethod
    def _execute_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms("sqlIntent", "executeTerms")

    @classmethod
    def _authoring_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms("sqlIntent", "authoringTerms")

    @classmethod
    def _sql_build_context(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms("sqlIntent", "sqlBuildContext")

    @classmethod
    def _sql_context_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms("sqlIntent", "sqlContextTerms")

    @classmethod
    def _sql_conversation_turn_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms(
            "sqlIntent",
            "sqlConversationTurnTerms",
        )

    @classmethod
    def _sql_review_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms("sqlIntent", "sqlReviewTerms")

    @classmethod
    def _sql_explain_terms(cls) -> tuple[str, ...]:
        return ChatSqlIntentVocabularyService.terms("sqlIntent", "sqlExplainTerms")

    @classmethod
    def _has_sql_context(cls, normalized: str) -> bool:
        return any(
            term in normalized
            for term in cls._sql_context_terms()
        ) or bool(
            re.search(
                r"\b(?:sa|sb|sc|sd|se|sf|sg|sh|si|sj|sk|sl|sm|sn|so|sp)[a-z]?\d{0,4}\b",
                normalized,
            )
        )

    @classmethod
    def is_sql_conversation_turn(cls, message: str | None) -> bool:
        """Turno de especialista SQL — não deve cair em text_task puro."""
        from app.domain.services.chat_presentation_format_refinement_service import (
            ChatPresentationFormatRefinementService,
        )
        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

        if ChatPresentationFormatRefinementService.looks_like_format_refinement(message):
            return False

        if ChatSqlSafetyService.looks_like_sql_payload(message):
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized or not cls._has_sql_context(normalized):
            return False

        if cls.is_authoring_request(message) or cls.should_auto_execute_sql(message):
            return True

        return any(term in normalized for term in cls._sql_conversation_turn_terms())

    @classmethod
    def router_sub_intent(cls, message: str | None) -> str | None:
        """Sub-intent SQL para o roteador (evita falso positivo em «sem executar»)."""
        from app.domain.services.chat_presentation_format_refinement_service import (
            ChatPresentationFormatRefinementService,
        )
        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService

        if ChatPresentationFormatRefinementService.looks_like_format_refinement(message):
            return None

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return None

        if not (
            ChatSqlSafetyService.looks_like_sql_payload(message)
            or cls._has_sql_context(normalized)
            or bool(re.search(r"\bsql\b", normalized))
        ):
            return None

        if cls.is_authoring_request(message):
            if any(term in normalized for term in cls._sql_review_terms()):
                return "sql_review"

            if any(term in normalized for term in cls._sql_explain_terms()):
                return "sql_explain"

            return "sql_generate"

        if cls.should_auto_execute_sql(message):
            return "sql_execute"

        if any(term in normalized for term in cls._sql_review_terms()):
            return "sql_review"

        if any(term in normalized for term in cls._sql_explain_terms()):
            return "sql_explain"

        return "sql_generate"

    @classmethod
    def is_authoring_request(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(term in normalized for term in cls._authoring_terms()):
            return True

        if "query" in normalized or "consulta sql" in normalized or "sql" in normalized:
            if any(ctx in normalized for ctx in cls._sql_build_context()):
                return True

        return False

    @classmethod
    def should_auto_execute_sql(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        from app.domain.services.chat_sql_safety_service import ChatSqlSafetyService
        from app.domain.services.chat_sql_operational_intent_service import (
            ChatSqlOperationalIntentService,
        )

        if ChatSqlOperationalIntentService.requires_sql_knowledge(message):
            return not cls.is_authoring_request(message)

        if any(term in normalized for term in cls._authoring_terms()):
            return False

        if any(term in normalized for term in cls._sql_review_terms()) and (
            ChatSqlSafetyService.looks_like_sql_payload(message)
            or cls._has_embedded_select(normalized)
        ):
            return False

        if any(term in normalized for term in cls._sql_explain_terms()) and (
            ChatSqlSafetyService.looks_like_sql_payload(message)
            or "query" in normalized
            or cls._has_embedded_select(normalized)
        ):
            return False

        if cls._has_embedded_select(normalized):
            return True

        if any(term in normalized for term in cls._execute_terms()):
            return True

        if "query" in normalized or "consulta sql" in normalized or "sql" in normalized:
            if any(ctx in normalized for ctx in cls._sql_build_context()):
                return False

        return False

    @classmethod
    def _has_embedded_select(cls, normalized: str) -> bool:
        return bool(re.search(r"\bselect\s+.+\bfrom\b", normalized, flags=re.I | re.S))
