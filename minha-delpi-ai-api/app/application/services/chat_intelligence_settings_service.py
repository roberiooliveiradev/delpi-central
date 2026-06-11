from dataclasses import dataclass

from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)
from app.infrastructure.config.settings import Settings


@dataclass(frozen=True)
class ChatIntelligenceSettings:
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


class ChatIntelligenceSettingsService:
    """Runtime de inteligência do chat: valores efetivos vêm sempre do .env (Settings)."""

    def __init__(
        self,
        settings_repository: AdminRuntimeSettingsRepositoryPort | None = None,
    ):
        self.settings_repository = settings_repository

    @classmethod
    def build_from_settings(cls) -> ChatIntelligenceSettings:
        return ChatIntelligenceSettings(
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
        )

    def resolve(self) -> ChatIntelligenceSettings:
        return self.build_from_settings()

    def payload_from_settings(self) -> dict:
        resolved = self.build_from_settings()

        return {
            "ragContextMinScore": resolved.rag_context_min_score,
            "externalActionSemanticMinScore": resolved.external_action_semantic_min_score,
            "externalActionSemanticRankEnabled": resolved.external_action_semantic_rank_enabled,
            "chatToolRouterEnabled": resolved.chat_tool_router_enabled,
            "chatHistorySummaryEnabled": resolved.chat_history_summary_enabled,
            "ragHybridEnabled": resolved.rag_hybrid_enabled,
            "ragRerankEnabled": resolved.rag_rerank_enabled,
            "ragFtsEnabled": resolved.rag_fts_enabled,
            "nativeToolCallingEnabled": resolved.native_tool_calling_enabled,
            "agenticLoopEnabled": resolved.agentic_loop_enabled,
            "agenticLoopMaxSteps": resolved.agentic_loop_max_steps,
            "webSearchEnabled": resolved.web_search_enabled,
        }

    def sync_from_environment(self) -> dict:
        """Espelha o .env no runtime admin (painel) — chamado no boot do container."""
        payload = self.payload_from_settings()

        if self.settings_repository is not None:
            self.settings_repository.save_chat_intelligence_settings(payload)

        return self.to_dict()

    def to_dict(self, settings: ChatIntelligenceSettings | None = None) -> dict:
        resolved = settings or self.resolve()

        return {
            "ragContextMinScore": resolved.rag_context_min_score,
            "externalActionSemanticMinScore": resolved.external_action_semantic_min_score,
            "externalActionSemanticRankEnabled": resolved.external_action_semantic_rank_enabled,
            "chatToolRouterEnabled": resolved.chat_tool_router_enabled,
            "chatHistorySummaryEnabled": resolved.chat_history_summary_enabled,
            "ragHybridEnabled": resolved.rag_hybrid_enabled,
            "ragRerankEnabled": resolved.rag_rerank_enabled,
            "ragFtsEnabled": resolved.rag_fts_enabled,
            "nativeToolCallingEnabled": resolved.native_tool_calling_enabled,
            "agenticLoopEnabled": resolved.agentic_loop_enabled,
            "agenticLoopMaxSteps": resolved.agentic_loop_max_steps,
            "webSearchEnabled": resolved.web_search_enabled,
            "source": "environment",
            "defaults": {
                "ragContextMinScore": Settings.RAG_CONTEXT_MIN_SCORE,
                "externalActionSemanticMinScore": Settings.EXTERNAL_ACTION_SEMANTIC_MIN_SCORE,
                "externalActionSemanticRankEnabled": Settings.EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED,
                "chatToolRouterEnabled": Settings.CHAT_TOOL_ROUTER_ENABLED,
                "chatHistorySummaryEnabled": Settings.CHAT_HISTORY_SUMMARY_ENABLED,
                "ragHybridEnabled": Settings.CHAT_RAG_HYBRID_ENABLED,
                "ragRerankEnabled": Settings.CHAT_RAG_RERANK_ENABLED,
                "ragFtsEnabled": Settings.CHAT_RAG_FTS_ENABLED,
                "nativeToolCallingEnabled": Settings.CHAT_NATIVE_TOOL_CALLING_ENABLED,
                "agenticLoopEnabled": Settings.CHAT_AGENTIC_LOOP_ENABLED,
                "agenticLoopMaxSteps": Settings.CHAT_AGENTIC_LOOP_MAX_STEPS,
                "webSearchEnabled": Settings.CHAT_WEB_SEARCH_ENABLED,
            },
        }

    def save(self, payload: dict) -> dict:
        """Persiste no admin runtime; o pipeline continua lendo só o .env via resolve()."""
        current = self.resolve()
        merged = {
            "ragContextMinScore": self._float(
                payload.get("ragContextMinScore"),
                current.rag_context_min_score,
            ),
            "externalActionSemanticMinScore": self._float(
                payload.get("externalActionSemanticMinScore"),
                current.external_action_semantic_min_score,
            ),
            "externalActionSemanticRankEnabled": self._bool(
                payload.get("externalActionSemanticRankEnabled"),
                current.external_action_semantic_rank_enabled,
            ),
            "chatToolRouterEnabled": self._bool(
                payload.get("chatToolRouterEnabled"),
                current.chat_tool_router_enabled,
            ),
            "chatHistorySummaryEnabled": self._bool(
                payload.get("chatHistorySummaryEnabled"),
                current.chat_history_summary_enabled,
            ),
            "ragHybridEnabled": self._bool(
                payload.get("ragHybridEnabled"),
                current.rag_hybrid_enabled,
            ),
            "ragRerankEnabled": self._bool(
                payload.get("ragRerankEnabled"),
                current.rag_rerank_enabled,
            ),
            "ragFtsEnabled": self._bool(
                payload.get("ragFtsEnabled"),
                current.rag_fts_enabled,
            ),
            "nativeToolCallingEnabled": self._bool(
                payload.get("nativeToolCallingEnabled"),
                current.native_tool_calling_enabled,
            ),
            "agenticLoopEnabled": self._bool(
                payload.get("agenticLoopEnabled"),
                current.agentic_loop_enabled,
            ),
            "agenticLoopMaxSteps": self._int(
                payload.get("agenticLoopMaxSteps"),
                current.agentic_loop_max_steps,
            ),
            "webSearchEnabled": self._bool(
                payload.get("webSearchEnabled"),
                current.web_search_enabled,
            ),
        }

        if self.settings_repository is not None:
            self.settings_repository.save_chat_intelligence_settings(merged)

        return self.to_dict()

    def _float(self, value, default: float) -> float:
        if value is None:
            return float(default)

        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _int(self, value, default: int) -> int:
        if value is None:
            return int(default)

        try:
            return max(1, min(int(value), 3))
        except (TypeError, ValueError):
            return int(default)

    def _bool(self, value, default: bool) -> bool:
        if value is None:
            return bool(default)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}

        return bool(value)
