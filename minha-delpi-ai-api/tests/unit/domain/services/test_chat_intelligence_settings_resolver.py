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
        operational_fast_path_enabled=True,
        external_action_direct_response_enabled=True,
        prefer_api_externa_provider=True,
        multi_action_enabled=True,
        pagination_auto_fetch_enabled=True,
        external_action_embedding_on_import=True,
        rag_prefer_keyword_search=True,
        rag_identity_question_min_score=0.22,
        fast_path_enabled=True,
        assistant_identity_direct_enabled=True,
        web_search_direct_response_enabled=True,
        web_search_auto_augment_enabled=True,
    )


def test_resolve_returns_defaults_when_stored_empty():
    resolved = resolve_chat_intelligence_settings(defaults=_defaults(), stored=None)

    assert resolved.rag_context_min_score == 0.35
    assert resolved.web_search_enabled is True
    assert resolved.external_action_embedding_on_import is True


def test_resolve_overrides_admin_fields():
    resolved = resolve_chat_intelligence_settings(
        defaults=_defaults(),
        stored={
            "webSearchEnabled": False,
            "externalActionEmbeddingOnImport": False,
            "ragContextMinScore": 0.5,
        },
    )

    assert resolved.web_search_enabled is False
    assert resolved.external_action_embedding_on_import is False
    assert resolved.rag_context_min_score == 0.5
    assert resolved.multi_action_enabled is True
