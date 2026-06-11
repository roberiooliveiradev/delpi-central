from app.domain.services.chat_intelligence_settings_resolver import (
    ChatIntelligenceSettingsSnapshot,
    resolve_chat_intelligence_settings,
)


def _defaults() -> ChatIntelligenceSettingsSnapshot:
    return ChatIntelligenceSettingsSnapshot(
        rag_context_min_score=0.35,
        external_action_semantic_min_score=0.42,
        external_action_semantic_rank_enabled=True,
        chat_tool_router_enabled=True,
        chat_history_summary_enabled=True,
        rag_hybrid_enabled=True,
        rag_rerank_enabled=True,
        rag_fts_enabled=True,
        native_tool_calling_enabled=False,
        agentic_loop_enabled=True,
        agentic_loop_max_steps=2,
        web_search_enabled=True,
    )


def test_resolve_returns_defaults_when_stored_empty():
    resolved = resolve_chat_intelligence_settings(defaults=_defaults(), stored=None)

    assert resolved.rag_context_min_score == 0.35
    assert resolved.web_search_enabled is True


def test_resolve_overrides_single_admin_field():
    resolved = resolve_chat_intelligence_settings(
        defaults=_defaults(),
        stored={"webSearchEnabled": False, "ragContextMinScore": 0.5},
    )

    assert resolved.web_search_enabled is False
    assert resolved.rag_context_min_score == 0.5
    assert resolved.chat_tool_router_enabled is True
