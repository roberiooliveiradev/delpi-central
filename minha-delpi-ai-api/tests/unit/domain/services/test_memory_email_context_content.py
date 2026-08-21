"""Contrato dos bundles memory_intent, user_context_items e email_intent."""

from __future__ import annotations

from app.domain.services.chat_email_intent_content_service import (
    ChatEmailIntentContentService,
)
from app.domain.services.chat_email_intent_service import ChatEmailIntentService
from app.domain.services.chat_memory_intent_content_service import (
    ChatMemoryIntentContentService,
)
from app.domain.services.chat_memory_ux_service import ChatMemoryUxService
from app.domain.services.chat_semantic_memory_intent_service import (
    ChatSemanticMemoryIntentService,
)
from app.domain.services.chat_user_context_items_content_service import (
    ChatUserContextItemsContentService,
)
from app.domain.services.chat_user_memory_durability_service import (
    ChatUserMemoryDurabilityService,
)


def test_memory_intent_patterns_compile():
    assert ChatMemoryIntentContentService.compile_pattern_list(
        "durability", "preferencePatterns"
    )
    assert ChatMemoryIntentContentService.compile_pattern(
        "semantic", "patterns", "docQuestion"
    )
    assert ChatMemoryIntentContentService.compile_pattern(
        "episodic", "patterns", "recall"
    )
    assert ChatMemoryIntentContentService.compile_pattern("ux", "patterns", "introspect")


def test_user_memory_durability_detects_preference():
    hit = ChatUserMemoryDurabilityService.detect(
        "De agora em diante sempre responda de forma objetiva."
    )
    assert hit is not None
    assert hit["type"] == "preference"


def test_semantic_memory_blocks_operational_stock():
    assert (
        ChatSemanticMemoryIntentService.should_enrich_semantic_retrieval(
            "estoque do produto 10080055"
        )
        is False
    )
    assert (
        ChatSemanticMemoryIntentService.should_enrich_semantic_retrieval(
            "como funciona a documentação de RBAC"
        )
        is True
    )


def test_memory_ux_introspection():
    assert ChatMemoryUxService.is_memory_introspection("qual contexto você está usando")


def test_user_context_items_content():
    assert ChatUserContextItemsContentService.compile_pattern("branch").search("filial 01")
    assert ChatUserContextItemsContentService.prompt_marker()
    assert ChatUserContextItemsContentService.limit_int("maxLabelChars", default=56) == 56


def test_email_intent_content_and_classify():
    assert ChatEmailIntentContentService.markers()
    assert ChatEmailIntentService.message_mentions_email("responda este e-mail")
    assert ChatEmailIntentService.classify_subtype("responda este e-mail") == "email_reply"
