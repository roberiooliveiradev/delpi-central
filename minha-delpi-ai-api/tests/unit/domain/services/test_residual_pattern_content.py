"""Contrato dos padrões residuais migrados (safety, quality, web security)."""

from __future__ import annotations

from app.application.services.chat_attachment_multi_compare_service import (
    ChatAttachmentMultiCompareService,
)
from app.application.services.chat_session_memory_service import ChatSessionMemoryService
from app.domain.services.chat_context_safety_filter_service import (
    ChatContextSafetyFilterService,
)
from app.domain.services.chat_email_quality_validator import ChatEmailQualityValidator
from app.domain.services.chat_entity_tracker_service import ChatEntityTrackerService
from app.domain.services.chat_memory_intent_content_service import (
    ChatMemoryIntentContentService,
)
from app.domain.services.chat_term_extraction_service import ChatTermExtractionService
from app.domain.services.chat_text_quality_content_service import (
    ChatTextQualityContentService,
)
from app.domain.services.chat_user_preference_manager_service import (
    ChatUserPreferenceManagerService,
)
from app.domain.services.chat_web_search_query_security_service import (
    ChatWebSearchQuerySecurityService,
)


def test_memory_intent_residual_patterns_compile():
    assert ChatMemoryIntentContentService.compile_pattern(
        "contextSafety", "patterns", "sensitive"
    )
    assert ChatMemoryIntentContentService.compile_pattern(
        "entityTracker", "patterns", "order"
    )
    assert ChatMemoryIntentContentService.compile_pattern(
        "preference", "patterns", "revoke"
    )
    assert ChatMemoryIntentContentService.compile_pattern("sessionClear", "pattern")


def test_entity_tracker_and_safety():
    snap = ChatEntityTrackerService.apply_to_snapshot(
        {}, message="estoque do pedido 12345 na filial 01"
    )
    focus = snap.get("operationalFocus") or {}
    assert focus.get("orderId") == "12345" or "12345" in str(focus)

    safe = ChatContextSafetyFilterService.apply_to_snapshot({}, message="minha senha é 123")
    assert (safe.get("conversationState") or {}).get("skipMemoryWrite") is True


def test_session_clear_and_preference_revoke():
    assert ChatSessionMemoryService.is_clear_context_request("limpe o contexto")
    assert ChatUserPreferenceManagerService._should_revoke(
        "volte ao comportamento padrão"
    )


def test_web_search_security_redacts_internal_price():
    result = ChatWebSearchQuerySecurityService.sanitize(
        "qual o preço interno R$ 12,50 do produto"
    )
    assert result.redacted is True


def test_email_and_text_quality_content():
    report = ChatEmailQualityValidator.validate(
        "Assunto: Solicitação de criação\n\nVenho por meio deste..."
    )
    assert isinstance(report, dict)

    assert ChatTextQualityContentService.compile_pattern("inventedSignature")
    assert ChatAttachmentMultiCompareService.wants_compare("cruzar os dois arquivos")


def test_term_definition_patterns():
    hit = ChatTermExtractionService.detect_definition_question("o que é RBAC?")
    assert hit is not None
