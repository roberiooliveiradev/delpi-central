from dataclasses import dataclass

from app.domain.ports.admin_runtime_settings_repository_port import (
    AdminRuntimeSettingsRepositoryPort,
)
from app.domain.services.chat_intelligence_settings_resolver import (
    ChatIntelligenceSettingsSnapshot,
    chat_intelligence_settings_to_payload,
    resolve_chat_intelligence_settings,
)
from app.infrastructure.config.chat_intelligence_settings_defaults import (
    build_chat_intelligence_defaults_from_settings,
)


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
    """Runtime de inteligência: admin prevalece; .env fornece apenas defaults iniciais."""

    def __init__(
        self,
        settings_repository: AdminRuntimeSettingsRepositoryPort | None = None,
    ):
        self.settings_repository = settings_repository

    @classmethod
    def build_defaults_from_settings(cls) -> ChatIntelligenceSettingsSnapshot:
        return build_chat_intelligence_defaults_from_settings()

    @classmethod
    def build_from_settings(cls) -> ChatIntelligenceSettings:
        snapshot = cls.build_defaults_from_settings()
        return cls._snapshot_to_dataclass(snapshot)

    def _load_stored_payload(self) -> dict | None:
        if self.settings_repository is None:
            return None

        return self.settings_repository.get_chat_intelligence_settings()

    def _resolve_snapshot(self) -> ChatIntelligenceSettingsSnapshot:
        return resolve_chat_intelligence_settings(
            defaults=self.build_defaults_from_settings(),
            stored=self._load_stored_payload(),
        )

    def resolve(self) -> ChatIntelligenceSettings:
        return self._snapshot_to_dataclass(self._resolve_snapshot())

    def payload_from_defaults(self) -> dict:
        return chat_intelligence_settings_to_payload(self.build_defaults_from_settings())

    def ensure_defaults_seeded(self) -> dict:
        """Grava defaults do Docker apenas quando ainda não há configuração admin."""
        stored = self._load_stored_payload()

        if stored:
            return self.to_dict()

        payload = self.payload_from_defaults()

        if self.settings_repository is not None:
            self.settings_repository.save_chat_intelligence_settings(payload)

        return self.to_dict()

    def sync_from_environment(self) -> dict:
        """Compatibilidade: delega para seed único — não sobrescreve admin."""
        return self.ensure_defaults_seeded()

    def to_dict(self, settings: ChatIntelligenceSettings | None = None) -> dict:
        resolved = settings or self.resolve()
        stored = self._load_stored_payload()
        defaults = self.build_defaults_from_settings()

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
            "source": "admin" if stored else "defaults",
            "defaults": chat_intelligence_settings_to_payload(defaults),
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

        return self.to_dict(self.resolve())

    @staticmethod
    def _snapshot_to_dataclass(
        snapshot: ChatIntelligenceSettingsSnapshot,
    ) -> ChatIntelligenceSettings:
        return ChatIntelligenceSettings(
            rag_context_min_score=snapshot.rag_context_min_score,
            external_action_semantic_min_score=snapshot.external_action_semantic_min_score,
            external_action_semantic_rank_enabled=snapshot.external_action_semantic_rank_enabled,
            chat_tool_router_enabled=snapshot.chat_tool_router_enabled,
            chat_history_summary_enabled=snapshot.chat_history_summary_enabled,
            rag_hybrid_enabled=snapshot.rag_hybrid_enabled,
            rag_rerank_enabled=snapshot.rag_rerank_enabled,
            rag_fts_enabled=snapshot.rag_fts_enabled,
            native_tool_calling_enabled=snapshot.native_tool_calling_enabled,
            agentic_loop_enabled=snapshot.agentic_loop_enabled,
            agentic_loop_max_steps=snapshot.agentic_loop_max_steps,
            web_search_enabled=snapshot.web_search_enabled,
        )

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
