from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChatIntelligenceSettingsSnapshot:
    rag_context_min_score: float
    external_action_semantic_min_score: float
    external_action_semantic_rank_enabled: bool
    chat_tool_router_enabled: bool
    chat_history_summary_enabled: bool
    rag_hybrid_enabled: bool
    rag_rerank_enabled: bool
    rag_fts_enabled: bool
    native_tool_calling_enabled: bool
    agentic_loop_enabled: bool
    agentic_loop_max_steps: int
    web_search_enabled: bool
    operational_fast_path_enabled: bool
    external_action_direct_response_enabled: bool
    prefer_api_externa_provider: bool
    multi_action_enabled: bool
    pagination_auto_fetch_enabled: bool
    external_action_embedding_on_import: bool
    rag_prefer_keyword_search: bool
    rag_identity_question_min_score: float
    fast_path_enabled: bool
    assistant_identity_direct_enabled: bool
    web_search_direct_response_enabled: bool
    web_search_auto_augment_enabled: bool


def chat_intelligence_settings_to_payload(
    settings: ChatIntelligenceSettingsSnapshot,
) -> dict[str, Any]:
    return {
        "ragContextMinScore": settings.rag_context_min_score,
        "externalActionSemanticMinScore": settings.external_action_semantic_min_score,
        "externalActionSemanticRankEnabled": settings.external_action_semantic_rank_enabled,
        "chatToolRouterEnabled": settings.chat_tool_router_enabled,
        "chatHistorySummaryEnabled": settings.chat_history_summary_enabled,
        "ragHybridEnabled": settings.rag_hybrid_enabled,
        "ragRerankEnabled": settings.rag_rerank_enabled,
        "ragFtsEnabled": settings.rag_fts_enabled,
        "nativeToolCallingEnabled": settings.native_tool_calling_enabled,
        "agenticLoopEnabled": settings.agentic_loop_enabled,
        "agenticLoopMaxSteps": settings.agentic_loop_max_steps,
        "webSearchEnabled": settings.web_search_enabled,
        "operationalFastPathEnabled": settings.operational_fast_path_enabled,
        "externalActionDirectResponseEnabled": settings.external_action_direct_response_enabled,
        "preferApiExternaProvider": settings.prefer_api_externa_provider,
        "multiActionEnabled": settings.multi_action_enabled,
        "paginationAutoFetchEnabled": settings.pagination_auto_fetch_enabled,
        "externalActionEmbeddingOnImport": settings.external_action_embedding_on_import,
        "ragPreferKeywordSearch": settings.rag_prefer_keyword_search,
        "ragIdentityQuestionMinScore": settings.rag_identity_question_min_score,
        "fastPathEnabled": settings.fast_path_enabled,
        "assistantIdentityDirectEnabled": settings.assistant_identity_direct_enabled,
        "webSearchDirectResponseEnabled": settings.web_search_direct_response_enabled,
        "webSearchAutoAugmentEnabled": settings.web_search_auto_augment_enabled,
    }


def resolve_chat_intelligence_settings(
    *,
    defaults: ChatIntelligenceSettingsSnapshot,
    stored: dict[str, Any] | None,
) -> ChatIntelligenceSettingsSnapshot:
    if not stored:
        return defaults

    return ChatIntelligenceSettingsSnapshot(
        rag_context_min_score=_float(
            stored.get("ragContextMinScore"),
            defaults.rag_context_min_score,
        ),
        external_action_semantic_min_score=_float(
            stored.get("externalActionSemanticMinScore"),
            defaults.external_action_semantic_min_score,
        ),
        external_action_semantic_rank_enabled=_bool(
            stored.get("externalActionSemanticRankEnabled"),
            defaults.external_action_semantic_rank_enabled,
        ),
        chat_tool_router_enabled=_bool(
            stored.get("chatToolRouterEnabled"),
            defaults.chat_tool_router_enabled,
        ),
        chat_history_summary_enabled=_bool(
            stored.get("chatHistorySummaryEnabled"),
            defaults.chat_history_summary_enabled,
        ),
        rag_hybrid_enabled=_bool(
            stored.get("ragHybridEnabled"),
            defaults.rag_hybrid_enabled,
        ),
        rag_rerank_enabled=_bool(
            stored.get("ragRerankEnabled"),
            defaults.rag_rerank_enabled,
        ),
        rag_fts_enabled=_bool(
            stored.get("ragFtsEnabled"),
            defaults.rag_fts_enabled,
        ),
        native_tool_calling_enabled=_bool(
            stored.get("nativeToolCallingEnabled"),
            defaults.native_tool_calling_enabled,
        ),
        agentic_loop_enabled=_bool(
            stored.get("agenticLoopEnabled"),
            defaults.agentic_loop_enabled,
        ),
        agentic_loop_max_steps=_loop_steps(
            stored.get("agenticLoopMaxSteps"),
            defaults.agentic_loop_max_steps,
        ),
        web_search_enabled=_bool(
            stored.get("webSearchEnabled"),
            defaults.web_search_enabled,
        ),
        operational_fast_path_enabled=_bool(
            stored.get("operationalFastPathEnabled"),
            defaults.operational_fast_path_enabled,
        ),
        external_action_direct_response_enabled=_bool(
            stored.get("externalActionDirectResponseEnabled"),
            defaults.external_action_direct_response_enabled,
        ),
        prefer_api_externa_provider=_bool(
            stored.get("preferApiExternaProvider"),
            defaults.prefer_api_externa_provider,
        ),
        multi_action_enabled=_bool(
            stored.get("multiActionEnabled"),
            defaults.multi_action_enabled,
        ),
        pagination_auto_fetch_enabled=_bool(
            stored.get("paginationAutoFetchEnabled"),
            defaults.pagination_auto_fetch_enabled,
        ),
        external_action_embedding_on_import=_bool(
            stored.get("externalActionEmbeddingOnImport"),
            defaults.external_action_embedding_on_import,
        ),
        rag_prefer_keyword_search=_bool(
            stored.get("ragPreferKeywordSearch"),
            defaults.rag_prefer_keyword_search,
        ),
        rag_identity_question_min_score=_score(
            stored.get("ragIdentityQuestionMinScore"),
            defaults.rag_identity_question_min_score,
        ),
        fast_path_enabled=_bool(
            stored.get("fastPathEnabled"),
            defaults.fast_path_enabled,
        ),
        assistant_identity_direct_enabled=_bool(
            stored.get("assistantIdentityDirectEnabled"),
            defaults.assistant_identity_direct_enabled,
        ),
        web_search_direct_response_enabled=_bool(
            stored.get("webSearchDirectResponseEnabled"),
            defaults.web_search_direct_response_enabled,
        ),
        web_search_auto_augment_enabled=_bool(
            stored.get("webSearchAutoAugmentEnabled"),
            defaults.web_search_auto_augment_enabled,
        ),
    )


def _float(value: Any, default: float) -> float:
    if value is None:
        return float(default)

    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _score(value: Any, default: float) -> float:
    parsed = _float(value, default)
    return max(0.0, min(parsed, 1.0))


def _loop_steps(value: Any, default: int) -> int:
    if value is None:
        return int(default)

    try:
        return max(1, min(int(value), 3))
    except (TypeError, ValueError):
        return int(default)


def _bool(value: Any, default: bool) -> bool:
    if value is None:
        return bool(default)

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}

    return bool(value)
