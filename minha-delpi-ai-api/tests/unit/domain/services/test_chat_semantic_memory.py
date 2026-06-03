"""Testes — memória semântica Fase 5."""

from __future__ import annotations

from app.domain.services.chat_context_ranking_service import ChatContextRankingService
from app.domain.services.chat_conversation_memory_service import (
    ChatConversationMemoryService,
)
from app.domain.services.chat_procedural_memory_provider_service import (
    ChatProceduralMemoryProviderService,
)
from app.domain.services.chat_semantic_memory_intent_service import (
    ChatSemanticMemoryIntentService,
)
from app.domain.services.chat_semantic_memory_retriever_service import (
    ChatSemanticMemoryRetrieverService,
)


def test_documentation_question_triggers_semantic_intent():
    assert ChatSemanticMemoryIntentService.should_enrich_semantic_retrieval(
        "Como funciona a autorização RBAC no DELPI?",
    )
    assert (
        ChatSemanticMemoryIntentService.intent_kind("Como funciona a autorização?")
        == "documentation"
    )


def test_operational_stock_does_not_trigger_semantic():
    assert not ChatSemanticMemoryIntentService.should_enrich_semantic_retrieval(
        "Qual o estoque do produto 10080001 na filial 01?",
    )


def test_procedural_hints_for_playbook_task():
    snapshot = {
        "conversationState": {
            "activeTask": {
                "type": "playbook_creation",
                "label": "playbook",
                "status": "in_progress",
            },
        },
    }
    hints = ChatProceduralMemoryProviderService.resolve_hints(snapshot=snapshot)

    assert hints
    assert any("playbook" in str(item.get("queryBoost") or "").lower() for item in hints)


def test_enriched_query_includes_task_and_procedural_boost():
    snapshot = ChatSemanticMemoryRetrieverService.apply_pre_turn(
        {
            "conversationState": {
                "activeTopic": "memória",
                "activeTask": {
                    "type": "playbook_creation",
                    "label": "playbook",
                    "objective": "playbook memória e contexto",
                },
            },
        },
        message="Como documentar preferências?",
    )

    query = ChatSemanticMemoryRetrieverService.build_enriched_query(
        "Como documentar preferências?",
        snapshot,
    )

    assert "playbook" in query.lower()
    assert "memória" in query.lower()


def test_rank_hits_orders_by_combined_score():
    hits = [
        {"title": "Baixo", "score": 0.4, "recencyScore": 0.3},
        {"title": "Alto", "score": 0.9, "recencyScore": 0.8, "taskMatch": True},
    ]
    ranked = ChatContextRankingService.rank_hits(
        hits,
        message="autorização",
        snapshot={
            "conversationState": {
                "activeTask": {"type": "documentation"},
            },
        },
    )

    assert ranked[0]["title"] == "Alto"


def test_attach_rag_result_populates_semantic_hits():
    snapshot = ChatSemanticMemoryRetrieverService.attach_rag_result(
        {},
        message="Como funciona autorização?",
        rag_context="Trecho sobre RBAC.",
        sources=[
            {
                "id": "1",
                "documentId": "d1",
                "title": "RBAC DELPI",
                "score": 0.88,
                "sourceType": "policy",
            },
        ],
        chunks=[
            {
                "id": "c1",
                "documentId": "d1",
                "title": "RBAC DELPI",
                "content": "Fluxo JWT e permission resolver.",
                "score": 0.88,
                "sourceType": "policy",
                "metadata": {"scope": "global"},
            },
        ],
    )

    assert snapshot["semanticMemoryUsed"] is True
    assert snapshot["semanticMemoryHits"]
    assert snapshot["semanticMemoryHits"][0]["snippet"]


def test_memory_pipeline_sets_semantic_requested():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="Qual playbook devo seguir para memória?",
        previous_messages=[],
    )

    assert snapshot.get("semanticMemoryRequested") is True
    assert snapshot.get("proceduralMemoryHints")
