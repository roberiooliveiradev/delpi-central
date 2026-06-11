from app.domain.services.chat_intelligence_settings_resolver import (
    ChatIntelligenceSettingsSnapshot,
)
from app.infrastructure.config.settings import Settings


def build_chat_intelligence_defaults_from_settings() -> ChatIntelligenceSettingsSnapshot:
    return ChatIntelligenceSettingsSnapshot(
        rag_context_min_score=float(Settings.RAG_CONTEXT_MIN_SCORE),
        external_action_semantic_min_score=float(
            Settings.EXTERNAL_ACTION_SEMANTIC_MIN_SCORE
        ),
        external_action_semantic_rank_enabled=bool(
            Settings.EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED
        ),
        chat_tool_router_enabled=bool(Settings.CHAT_TOOL_ROUTER_ENABLED),
        chat_history_summary_enabled=bool(Settings.CHAT_HISTORY_SUMMARY_ENABLED),
        rag_hybrid_enabled=bool(Settings.CHAT_RAG_HYBRID_ENABLED),
        rag_rerank_enabled=bool(Settings.CHAT_RAG_RERANK_ENABLED),
        rag_fts_enabled=bool(Settings.CHAT_RAG_FTS_ENABLED),
        native_tool_calling_enabled=bool(Settings.CHAT_NATIVE_TOOL_CALLING_ENABLED),
        agentic_loop_enabled=bool(Settings.CHAT_AGENTIC_LOOP_ENABLED),
        agentic_loop_max_steps=max(
            1,
            min(int(Settings.CHAT_AGENTIC_LOOP_MAX_STEPS), 3),
        ),
        web_search_enabled=bool(Settings.CHAT_WEB_SEARCH_ENABLED),
        operational_fast_path_enabled=bool(Settings.CHAT_OPERATIONAL_FAST_PATH_ENABLED),
        external_action_direct_response_enabled=bool(
            Settings.CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED
        ),
        prefer_api_externa_provider=bool(Settings.CHAT_PREFER_API_EXTERNA_PROVIDER),
        multi_action_enabled=bool(Settings.CHAT_MULTI_ACTION_ENABLED),
        pagination_auto_fetch_enabled=bool(Settings.CHAT_PAGINATION_AUTO_FETCH_ENABLED),
        external_action_embedding_on_import=bool(
            Settings.EXTERNAL_ACTION_EMBEDDING_ON_IMPORT
        ),
        rag_prefer_keyword_search=bool(Settings.CHAT_RAG_PREFER_KEYWORD_SEARCH),
        rag_identity_question_min_score=float(Settings.RAG_IDENTITY_QUESTION_MIN_SCORE),
        fast_path_enabled=bool(Settings.CHAT_FAST_PATH_ENABLED),
        assistant_identity_direct_enabled=bool(
            Settings.CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED
        ),
        web_search_direct_response_enabled=bool(
            Settings.CHAT_WEB_SEARCH_DIRECT_RESPONSE_ENABLED
        ),
        web_search_auto_augment_enabled=bool(
            Settings.CHAT_WEB_SEARCH_AUTO_AUGMENT_ENABLED
        ),
    )
