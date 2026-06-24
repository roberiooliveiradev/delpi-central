"""Loader JSON `operational_narrative_synthesis` — perfis e policies de síntese LLM."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "operational_narrative_synthesis"


class ChatOperationalNarrativeSynthesisContentService:
    @classmethod
    def evidence_first_profile_keys(cls) -> frozenset[str]:
        node = ChatAssistantContentService.list(_BUNDLE, "evidenceFirstProfileKeys")

        return frozenset(str(item).strip() for item in node if str(item).strip())

    @classmethod
    def entity_profile_map(cls) -> dict[str, str]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "entityProfileMap")

        if not isinstance(node, dict):
            return {}

        return {
            str(key).strip(): str(value).strip()
            for key, value in node.items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def path_markers(cls) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, "pathMarkers"))

    @classmethod
    def playbook_path_markers(cls) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, "playbookPathMarkers"))

    @classmethod
    def sql_path_markers(cls) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, "sqlPathMarkers"))

    @classmethod
    def kpi_path_markers(cls) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, "kpiPathMarkers"))

    @classmethod
    def structure_exclusivity_path_markers(cls) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, "structureExclusivityPathMarkers"))

    @classmethod
    def narrative_markers(cls) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, "narrativeMarkers"))

    @classmethod
    def factual_narrow_terms(cls) -> tuple[str, ...]:
        return tuple(ChatAssistantContentService.list(_BUNDLE, "factualNarrowTerms"))

    @classmethod
    def synthesis_policy(cls, kind: str, response_mode: str) -> str:
        policy = ChatAssistantContentService.get(
            _BUNDLE,
            "synthesisPolicies",
            kind,
            response_mode,
            default="",
        )

        return str(policy or "").strip()
