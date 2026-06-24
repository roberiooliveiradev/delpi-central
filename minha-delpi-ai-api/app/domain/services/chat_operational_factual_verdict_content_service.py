"""Loader JSON `operational_factual_verdict` — regras de veredito factual por profileKey."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "operational_factual_verdict"


class ChatOperationalFactualVerdictContentService:
    @classmethod
    def profile_keys(cls) -> list[str]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "profiles")

        if not isinstance(node, dict):
            return []

        return [str(key).strip() for key in node if str(key).strip()]

    @classmethod
    def profile_node(cls, profile_key: str) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "profiles", profile_key)

        return node if isinstance(node, dict) else {}

    @classmethod
    def path_markers(cls, profile_key: str) -> list[str]:
        raw = cls.profile_node(profile_key).get("pathMarkers")

        if not isinstance(raw, list):
            return []

        return [str(item).strip() for item in raw if str(item or "").strip()]

    @classmethod
    def fidelity_rule(cls, profile_key: str) -> str:
        return str(cls.profile_node(profile_key).get("fidelityRule") or "").strip()

    @classmethod
    def quality_gap_key(cls, profile_key: str) -> str:
        return str(cls.profile_node(profile_key).get("qualityGapKey") or "").strip()

    @classmethod
    def llm_fact(cls, profile_key: str, key: str, **values) -> str:
        return ChatAssistantContentService.format(
            _BUNDLE,
            "profiles",
            profile_key,
            "llmFacts",
            key,
            default="",
            **values,
        ).strip()

    @classmethod
    def markdown_verdict_line_prefix(cls, profile_key: str) -> str:
        return str(
            ChatAssistantContentService.get(
                _BUNDLE,
                "profiles",
                profile_key,
                "llmFacts",
                "markdownVerdictLinePrefix",
                default="**resposta:**",
            )
            or "**resposta:**"
        ).strip()

    @classmethod
    def kpi_label_markers(cls, profile_key: str) -> list[str]:
        raw = cls.profile_node(profile_key).get("scalarFromKpi", {})

        if not isinstance(raw, dict):
            return []

        markers = raw.get("labelMarkers")

        if not isinstance(markers, list):
            return []

        return [str(item).strip() for item in markers if str(item or "").strip()]

    @classmethod
    def _factual_coherence_node(cls, profile_key: str) -> dict[str, Any]:
        node = cls.profile_node(profile_key).get("factualCoherence")

        return node if isinstance(node, dict) else {}

    @classmethod
    def contradiction_triggers(cls, profile_key: str) -> list[str]:
        raw = cls._factual_coherence_node(profile_key).get("contradictionTriggers")

        if not isinstance(raw, list):
            return []

        return [str(item).strip() for item in raw if str(item or "").strip()]

    @classmethod
    def positive_markers(cls, profile_key: str) -> list[str]:
        raw = cls._factual_coherence_node(profile_key).get("positiveMarkers")

        if not isinstance(raw, list):
            return []

        return [str(item).strip() for item in raw if str(item or "").strip()]

    @classmethod
    def shared_markers(cls, profile_key: str) -> list[str]:
        raw = cls._factual_coherence_node(profile_key).get("sharedMarkers")

        if not isinstance(raw, list):
            return []

        return [str(item).strip() for item in raw if str(item or "").strip()]

    @classmethod
    def verdict_no_markers(cls, profile_key: str) -> list[str]:
        raw = cls._factual_coherence_node(profile_key).get("verdictNoMarkers")

        if not isinstance(raw, list):
            return []

        return [str(item).strip() for item in raw if str(item or "").strip()]

    @classmethod
    def defined_with_shared_marker(cls, profile_key: str) -> str:
        return str(
            cls._factual_coherence_node(profile_key).get("definedWithSharedMarker")
            or "definida"
        ).strip()

    @classmethod
    def coherence_gap_detail(cls, profile_key: str, key: str) -> str:
        node = cls._factual_coherence_node(profile_key).get("gapDetails", {})

        if not isinstance(node, dict):
            return ""

        return str(node.get(key) or "").strip()
