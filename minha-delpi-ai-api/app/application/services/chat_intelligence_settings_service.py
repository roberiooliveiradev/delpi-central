from dataclasses import dataclass

from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.postgres_admin_runtime_settings_repository import (
    CHAT_INTELLIGENCE_SETTINGS_KEY,
    PostgresAdminRuntimeSettingsRepository,
)


@dataclass(frozen=True)
class ChatIntelligenceSettings:
    rag_context_min_score: float
    external_action_semantic_min_score: float
    external_action_semantic_rank_enabled: bool
    chat_tool_router_enabled: bool
    chat_history_summary_enabled: bool


class ChatIntelligenceSettingsService:
    def __init__(
        self,
        settings_repository: PostgresAdminRuntimeSettingsRepository | None = None,
    ):
        self.settings_repository = settings_repository or PostgresAdminRuntimeSettingsRepository()

    def resolve(self) -> ChatIntelligenceSettings:
        stored = self.settings_repository.get_chat_intelligence_settings() or {}

        return ChatIntelligenceSettings(
            rag_context_min_score=self._float(
                stored.get("ragContextMinScore"),
                Settings.RAG_CONTEXT_MIN_SCORE,
            ),
            external_action_semantic_min_score=self._float(
                stored.get("externalActionSemanticMinScore"),
                Settings.EXTERNAL_ACTION_SEMANTIC_MIN_SCORE,
            ),
            external_action_semantic_rank_enabled=self._bool(
                stored.get("externalActionSemanticRankEnabled"),
                Settings.EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED,
            ),
            chat_tool_router_enabled=self._bool(
                stored.get("chatToolRouterEnabled"),
                Settings.CHAT_TOOL_ROUTER_ENABLED,
            ),
            chat_history_summary_enabled=self._bool(
                stored.get("chatHistorySummaryEnabled"),
                Settings.CHAT_HISTORY_SUMMARY_ENABLED,
            ),
        )

    def to_dict(self, settings: ChatIntelligenceSettings | None = None) -> dict:
        resolved = settings or self.resolve()

        return {
            "ragContextMinScore": resolved.rag_context_min_score,
            "externalActionSemanticMinScore": resolved.external_action_semantic_min_score,
            "externalActionSemanticRankEnabled": resolved.external_action_semantic_rank_enabled,
            "chatToolRouterEnabled": resolved.chat_tool_router_enabled,
            "chatHistorySummaryEnabled": resolved.chat_history_summary_enabled,
            "defaults": {
                "ragContextMinScore": Settings.RAG_CONTEXT_MIN_SCORE,
                "externalActionSemanticMinScore": Settings.EXTERNAL_ACTION_SEMANTIC_MIN_SCORE,
                "externalActionSemanticRankEnabled": Settings.EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED,
                "chatToolRouterEnabled": Settings.CHAT_TOOL_ROUTER_ENABLED,
                "chatHistorySummaryEnabled": Settings.CHAT_HISTORY_SUMMARY_ENABLED,
            },
        }

    def save(self, payload: dict) -> dict:
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
        }

        self.settings_repository.save_chat_intelligence_settings(merged)

        return self.to_dict(self.resolve())

    def _float(self, value, default: float) -> float:
        if value is None:
            return float(default)

        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    def _bool(self, value, default: bool) -> bool:
        if value is None:
            return bool(default)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}

        return bool(value)
