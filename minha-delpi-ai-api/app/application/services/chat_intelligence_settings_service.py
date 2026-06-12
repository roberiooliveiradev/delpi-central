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

_PAYLOAD_BOOL_KEYS = (
    "externalActionSemanticRankEnabled",
    "chatToolRouterEnabled",
    "chatHistorySummaryEnabled",
    "ragHybridEnabled",
    "ragRerankEnabled",
    "ragFtsEnabled",
    "nativeToolCallingEnabled",
    "agenticLoopEnabled",
    "webSearchEnabled",
    "operationalFastPathEnabled",
    "externalActionDirectResponseEnabled",
    "preferApiExternaProvider",
    "multiActionEnabled",
    "paginationAutoFetchEnabled",
    "externalActionEmbeddingOnImport",
    "ragPreferKeywordSearch",
    "fastPathEnabled",
    "assistantIdentityDirectEnabled",
    "webSearchDirectResponseEnabled",
    "webSearchAutoAugmentEnabled",
)

_PAYLOAD_FLOAT_KEYS = (
    "ragContextMinScore",
    "externalActionSemanticMinScore",
    "ragIdentityQuestionMinScore",
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
        return cls._snapshot_to_dataclass(cls.build_defaults_from_settings())

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
        snapshot = self._dataclass_to_snapshot(resolved)

        return {
            **chat_intelligence_settings_to_payload(snapshot),
            "source": "admin" if stored else "defaults",
            "defaults": chat_intelligence_settings_to_payload(defaults),
        }

    def save(self, payload: dict) -> dict:
        current = chat_intelligence_settings_to_payload(self._resolve_snapshot())
        merged = dict(current)

        for key in _PAYLOAD_FLOAT_KEYS:
            if key in payload:
                merged[key] = self._score(
                    payload.get(key),
                    float(merged.get(key, 0)),
                )

        if "agenticLoopMaxSteps" in payload:
            merged["agenticLoopMaxSteps"] = self._int(
                payload.get("agenticLoopMaxSteps"),
                int(merged.get("agenticLoopMaxSteps", 2)),
            )

        for key in _PAYLOAD_BOOL_KEYS:
            if key in payload:
                merged[key] = self._bool(
                    payload.get(key),
                    bool(merged.get(key, False)),
                )

        if self.settings_repository is not None:
            self.settings_repository.save_chat_intelligence_settings(merged)

        return self.to_dict()

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
            operational_fast_path_enabled=snapshot.operational_fast_path_enabled,
            external_action_direct_response_enabled=snapshot.external_action_direct_response_enabled,
            prefer_api_externa_provider=snapshot.prefer_api_externa_provider,
            multi_action_enabled=snapshot.multi_action_enabled,
            pagination_auto_fetch_enabled=snapshot.pagination_auto_fetch_enabled,
            external_action_embedding_on_import=snapshot.external_action_embedding_on_import,
            rag_prefer_keyword_search=snapshot.rag_prefer_keyword_search,
            rag_identity_question_min_score=snapshot.rag_identity_question_min_score,
            fast_path_enabled=snapshot.fast_path_enabled,
            assistant_identity_direct_enabled=snapshot.assistant_identity_direct_enabled,
            web_search_direct_response_enabled=snapshot.web_search_direct_response_enabled,
            web_search_auto_augment_enabled=snapshot.web_search_auto_augment_enabled,
        )

    @staticmethod
    def _dataclass_to_snapshot(
        settings: ChatIntelligenceSettings,
    ) -> ChatIntelligenceSettingsSnapshot:
        return ChatIntelligenceSettingsSnapshot(
            rag_context_min_score=settings.rag_context_min_score,
            external_action_semantic_min_score=settings.external_action_semantic_min_score,
            external_action_semantic_rank_enabled=settings.external_action_semantic_rank_enabled,
            chat_tool_router_enabled=settings.chat_tool_router_enabled,
            chat_history_summary_enabled=settings.chat_history_summary_enabled,
            rag_hybrid_enabled=settings.rag_hybrid_enabled,
            rag_rerank_enabled=settings.rag_rerank_enabled,
            rag_fts_enabled=settings.rag_fts_enabled,
            native_tool_calling_enabled=settings.native_tool_calling_enabled,
            agentic_loop_enabled=settings.agentic_loop_enabled,
            agentic_loop_max_steps=settings.agentic_loop_max_steps,
            web_search_enabled=settings.web_search_enabled,
            operational_fast_path_enabled=settings.operational_fast_path_enabled,
            external_action_direct_response_enabled=settings.external_action_direct_response_enabled,
            prefer_api_externa_provider=settings.prefer_api_externa_provider,
            multi_action_enabled=settings.multi_action_enabled,
            pagination_auto_fetch_enabled=settings.pagination_auto_fetch_enabled,
            external_action_embedding_on_import=settings.external_action_embedding_on_import,
            rag_prefer_keyword_search=settings.rag_prefer_keyword_search,
            rag_identity_question_min_score=settings.rag_identity_question_min_score,
            fast_path_enabled=settings.fast_path_enabled,
            assistant_identity_direct_enabled=settings.assistant_identity_direct_enabled,
            web_search_direct_response_enabled=settings.web_search_direct_response_enabled,
            web_search_auto_augment_enabled=settings.web_search_auto_augment_enabled,
        )

    def _score(self, value, default: float) -> float:
        if value is None:
            return max(0.0, min(float(default), 1.0))

        try:
            return max(0.0, min(float(value), 1.0))
        except (TypeError, ValueError):
            return max(0.0, min(float(default), 1.0))

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
