"""Métricas de eficiência §30 — resposta direta, fallback, tools/RAG/LLM evitados."""

from app.domain.services.chat_feedback_context_service import (
    ChatFeedbackContextService,
)
from app.domain.services.chat_intent_router_metrics_service import (
    ChatIntentRouterMetricsService,
)
from app.domain.services.chat_response_metadata_service import (
    ChatResponseMetadataService,
)


def test_efficiency_flags_for_direct_simple_turn():
    metadata = {
        "intentRouting": {
            "intent": "identity",
            "subIntent": "assistant_identity",
            "requiresLlm": False,
            "requiresTool": False,
            "decision": "direct_answer",
        },
    }
    snapshot = ChatFeedbackContextService.snapshot_from_assistant_metadata(metadata)

    assert snapshot["directAnswer"] is True
    assert snapshot["llmSkipped"] is True
    assert snapshot["toolSkipped"] is True
    assert snapshot["simpleTurn"] is True
    assert snapshot["fallback"] is False


def test_efficiency_flags_for_unclear_fallback():
    metadata = {
        "intentRouting": {
            "intent": "clarification",
            "subIntent": "unclear",
            "requiresLlm": False,
            "decision": "direct_answer",
        },
    }
    snapshot = ChatFeedbackContextService.snapshot_from_assistant_metadata(metadata)

    assert snapshot["fallback"] is True
    assert snapshot["simpleTurn"] is True


def test_efficiency_flags_for_tool_turn():
    metadata = {
        "intentRouting": {
            "intent": "operational_query",
            "requiresLlm": True,
            "requiresTool": True,
            "decision": "use_tool",
        },
        "toolCalls": [{"metadata": {"path": "/produtos"}}],
        "rag": {"sources": [{"id": "a"}]},
    }
    snapshot = ChatFeedbackContextService.snapshot_from_assistant_metadata(metadata)

    assert snapshot["directAnswer"] is False
    assert snapshot["toolSkipped"] is False
    assert snapshot["ragSkipped"] is False
    assert snapshot["simpleTurn"] is False


def test_response_quality_mirror_includes_efficiency():
    metadata = {
        "intentRouting": {
            "intent": "small_talk",
            "requiresLlm": False,
            "decision": "direct_answer",
        },
        "adminDebug": {},
    }
    ChatResponseMetadataService.attach_to_assistant_metadata(metadata)
    quality = metadata["adminDebug"]["responseQuality"]

    assert quality["directAnswer"] is True
    assert quality["simpleTurn"] is True
    assert quality["toolSkipped"] is True


def test_router_aggregation_counts_simple_and_fallback():
    entries = [
        {"snapshot": {"intent": "identity", "requiresLlm": False, "decision": "direct_answer"}},
        {"snapshot": {"intent": "small_talk", "requiresLlm": False, "decision": "direct_answer"}},
        {
            "snapshot": {
                "intent": "clarification",
                "subIntent": "unclear",
                "requiresLlm": False,
                "decision": "llm_fallback",
            }
        },
        {"snapshot": {"intent": "operational_query", "requiresLlm": True, "decision": "use_tool"}},
    ]
    agg = ChatIntentRouterMetricsService.aggregate_snapshots(
        entries, hours=24, since_iso="2026-06-03T00:00:00Z"
    )

    assert agg["simpleTurnCount"] == 3
    assert agg["fallbackCount"] == 1
    assert agg["directAnswerCount"] == 3
