"""Catálogo de ajuda para o painel do chat — Autoajuda Fase 4."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from app.application.services.assistant_capabilities_registry import (
    AssistantCapabilitiesRegistry,
)
from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.postgres_external_action_repository import (
    PostgresExternalActionRepository,
)

_CATEGORY_LABELS: dict[str, str] = {
    "chat_basic": "Chat e agentes",
    "operational": "Consultas operacionais",
    "indicators": "Indicadores e KPIs",
    "knowledge": "Conhecimento e arquivos",
    "visualization": "Gráficos e lousa",
    "text": "Textos e comunicação",
}

_QUICK_PROMPTS: list[dict[str, str]] = [
    {"id": "capabilities", "label": "O que posso fazer?", "query": "O que você pode fazer?"},
    {"id": "how_to", "label": "Como usar", "query": "Como faço uma boa pergunta?"},
    {"id": "examples", "label": "Exemplos", "query": "Me dê exemplos de perguntas úteis"},
    {"id": "news", "label": "Novidades", "query": "O que mudou?"},
    {"id": "limits", "label": "Limites", "query": "O que você não consegue fazer?"},
    {"id": "permissions", "label": "Permissões", "query": "Por que não consigo consultar estoque?"},
]


class ChatAssistantCatalogService:
    def __init__(
        self,
        agent_repository: ChatAgentRepositoryPort | None = None,
        action_repository: PostgresExternalActionRepository | None = None,
        intelligence_settings: ChatIntelligenceSettingsService | None = None,
    ):
        self.agent_repository = agent_repository
        self.action_repository = action_repository or PostgresExternalActionRepository()
        self.intelligence_settings = (
            intelligence_settings or ChatIntelligenceSettingsService()
        )

    def build_response(
        self,
        *,
        user_id: UUID,
        query: str | None = None,
        agent_id: str | None = None,
        limit: int = 24,
        user_permissions: set[str] | None = None,
        is_superadmin: bool = False,
        can_use_tools: bool | None = None,
        can_open_admin: bool | None = None,
    ) -> dict[str, Any]:
        normalized_query = str(query or "").strip()
        web_search_enabled = self._resolve_web_search_enabled()
        allowed_action_ids: list[str] = []
        agent_name: str | None = None

        if agent_id and self.agent_repository:
            parsed = self._parse_agent_id(agent_id)

            if parsed:
                agent = self.agent_repository.get_enabled_by_id(parsed, user_id=user_id)

                if agent:
                    agent_name = str(agent.name or "").strip() or None
                    allowed_action_ids = self._allowed_action_ids(agent, user_id)

        action_catalog = self._load_action_catalog()
        availability = AssistantCapabilitiesRegistry.resolve_availability(
            allowed_action_ids=allowed_action_ids,
            action_catalog=action_catalog,
            web_search_enabled=web_search_enabled,
            user_permissions=user_permissions,
            is_superadmin=is_superadmin,
            can_use_tools=can_use_tools,
        )

        if normalized_query:
            features = AssistantCapabilitiesRegistry.search(normalized_query, limit=limit)
        else:
            features = AssistantCapabilitiesRegistry.list_features()[:limit]

        profile_blocked_ids = {
            str(item.get("id") or "").strip()
            for item in availability.get("requiresProfilePermission") or []
            if str(item.get("id") or "").strip()
        }

        if profile_blocked_ids:
            features = [
                item
                for item in features
                if str(item.get("id") or "").strip() not in profile_blocked_ids
            ]

        categories = self._group_by_category(features)
        highlights = AssistantCapabilitiesRegistry.list_contextual_highlights(limit=3)

        if profile_blocked_ids:
            highlights = [
                item
                for item in highlights
                if str(item.get("featureId") or "").strip() not in profile_blocked_ids
            ]

        return {
            "version": AssistantCapabilitiesRegistry.catalog_version(),
            "query": normalized_query or None,
            "webSearchEnabled": web_search_enabled,
            "agentId": str(agent_id).strip() if agent_id else None,
            "agentName": agent_name,
            "features": features,
            "categories": categories,
            "availability": availability,
            "quickPrompts": list(_QUICK_PROMPTS),
            "categoryLabels": dict(_CATEGORY_LABELS),
            "releaseNotesPreview": AssistantCapabilitiesRegistry.format_release_notes_answer(
                limit=4,
            ),
            "releaseVersion": AssistantCapabilitiesRegistry.latest_release_version(),
            "contextualHighlights": highlights,
            "userContext": {
                "canUseTools": AssistantCapabilitiesRegistry.user_can_use_tools(
                    permissions={str(item).strip() for item in (user_permissions or []) if str(item).strip()},
                    is_superadmin=is_superadmin,
                    can_use_tools=can_use_tools,
                ),
                "isSuperadmin": bool(is_superadmin),
                "canOpenAdmin": bool(can_open_admin) if can_open_admin is not None else None,
            },
        }

    @classmethod
    def _group_by_category(cls, features: list[dict[str, Any]]) -> list[dict[str, Any]]:
        buckets: dict[str, list[dict[str, Any]]] = {}

        for feature in features:
            category = str(feature.get("category") or "chat_basic").strip() or "chat_basic"
            buckets.setdefault(category, []).append(feature)

        ordered_keys = [
            key
            for key in _CATEGORY_LABELS
            if key in buckets
        ] + [key for key in buckets if key not in _CATEGORY_LABELS]

        return [
            {
                "id": key,
                "label": _CATEGORY_LABELS.get(key, key.replace("_", " ").title()),
                "features": buckets[key],
            }
            for key in ordered_keys
        ]

    def _load_action_catalog(self) -> list[dict[str, Any]]:
        try:
            from flask import has_app_context

            if has_app_context():
                return self.action_repository.list_actions() or []
        except Exception:
            pass

        return []

    def _resolve_web_search_enabled(self) -> bool:
        try:
            from flask import has_app_context

            if has_app_context():
                return self.intelligence_settings.resolve().web_search_enabled
        except Exception:
            pass

        return Settings.CHAT_WEB_SEARCH_ENABLED

    @staticmethod
    def _parse_agent_id(value: str | None) -> UUID | None:
        token = str(value or "").strip()

        if not token:
            return None

        try:
            return UUID(token)
        except ValueError:
            return None

    def _allowed_action_ids(self, agent, user_id: UUID) -> list[str]:
        if not self.agent_repository:
            return []

        configured = self.agent_repository.list_enabled_action_ids(
            agent_id=agent.id,
            user_id=user_id,
        )

        if configured:
            return configured

        metadata = agent.metadata or {}
        allowed = metadata.get("allowed_actions") or metadata.get("allowedActions")

        if isinstance(allowed, list):
            return [str(item) for item in allowed if str(item).strip()]

        return []
