"""Testes — contexto avançado Fase 7."""

from __future__ import annotations

from app.domain.services.chat_advanced_context_service import ChatAdvancedContextService
from app.domain.services.chat_context_safety_filter_service import (
    ChatContextSafetyFilterService,
)
from app.domain.services.chat_conversation_memory_service import (
    ChatConversationMemoryService,
)
from app.domain.services.chat_memory_contradiction_service import (
    ChatMemoryContradictionService,
)


def test_m10_contradiction_short_to_long_preference():
    snapshot = ChatMemoryContradictionService.apply_to_snapshot(
        {
            "behaviorInstructions": {"answerLength": "short"},
            "conversationState": {"activeTask": {"type": "playbook_creation", "status": "in_progress"}},
        },
        message="Daqui pra frente quero respostas completas e detalhadas",
    )

    assert snapshot.get("memoryContradictionResolved")
    assert snapshot["behaviorInstructions"].get("answerLength") == "long"


def test_m18_safety_gates_write_on_sensitive_message():
    snapshot = ChatContextSafetyFilterService.apply_to_snapshot(
        {"conversationState": {}},
        message="minha senha é abc123",
    )

    assert snapshot.get("memoryWriteGated") is True
    assert not ChatContextSafetyFilterService.should_allow_persist(snapshot)


def test_m19_forgetting_on_topic_change():
    snapshot = ChatAdvancedContextService.apply_pre_turn(
        {
            "preferencesTopicChanged": True,
            "previousProductCodes": ["10080001", "10080002", "10080003", "10080004"],
            "episodicMemory": [{"episodeId": "e1"}, {"episodeId": "e2"}, {"episodeId": "e3"}],
            "referenceHints": {"lastSqlSnippet": "SELECT 1"},
            "conversationState": {"activeTopic": "e-mail"},
        },
        message="agora vamos falar de e-mail",
    )

    assert len(snapshot.get("previousProductCodes") or []) <= 1
    assert len(snapshot.get("episodicMemory") or []) <= 2
    assert snapshot.get("forgottenMemoryKeys")


def test_knowledge_graph_builds_nodes():
    snapshot = ChatAdvancedContextService.apply_pre_turn(
        {
            "conversationState": {
                "activeTopic": "estoque",
                "activeTask": {"type": "stock_lookup", "label": "estoque"},
            },
            "operationalFocus": {"productCode": "10080001"},
        },
        message="e os fornecedores?",
    )

    graph = snapshot.get("memoryGraph") or {}

    assert graph.get("nodeCount", 0) >= 2


def test_knowledge_graph_hides_internal_operational_focus_keys():
    from app.domain.services.chat_memory_knowledge_graph_service import (
        ChatMemoryKnowledgeGraphService,
    )

    graph = ChatMemoryKnowledgeGraphService.build(
        {
            "operationalFocus": {
                "productCode": "90260205",
                "productCodeSource": "tool",
                "lastSqlSnippet": "select 1",
            },
            "conversationState": {"activeTopic": "structure_lookup"},
        }
    )
    labels = [node.get("label") for node in graph.get("nodes") or []]

    assert "90260205" in labels
    assert not any("productCodeSource" in str(label) for label in labels)
    assert not any("lastSqlSnippet" in str(label) for label in labels)
    assert "structure_lookup" in labels


def test_pipeline_includes_memory_context_debug():
    snapshot = ChatConversationMemoryService.build_pre_turn(
        message="responda em tabela",
        previous_messages=[],
    )

    debug = snapshot.get("memoryContextDebug") or {}

    assert "layers" in debug
    assert "writeAllowed" in debug
