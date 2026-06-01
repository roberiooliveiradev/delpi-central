"""Telemetria e metadata de autoajuda — Playbook 04, Fase 5."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("minha-delpi-ai-api.self-help")

_IDENTITY_HELP_CATEGORIES = frozenset({"usage", "goodQuestion", "limits"})


class ChatHelpSelfHelpTelemetryService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str,
        workspace_context: dict | None = None,
        had_direct_answer: bool = False,
    ) -> None:
        if not had_direct_answer:
            return

        from app.application.services.chat_assistant_identity_service import (
            ChatAssistantIdentityService,
        )
        from app.application.services.chat_capabilities_service import (
            ChatCapabilitiesService,
        )

        is_capability = ChatCapabilitiesService.is_capability_inquiry(message)
        identity_category = ChatAssistantIdentityService.classify(message)
        is_identity_help = identity_category in _IDENTITY_HELP_CATEGORIES

        if not is_capability and not is_identity_help:
            return

        topic = cls._resolve_topic(
            message=message,
            identity_category=identity_category,
            is_capability=is_capability,
        )
        workspace = workspace_context or {}
        agent = workspace.get("agent") if isinstance(workspace.get("agent"), dict) else {}
        agent_name = str(agent.get("name") or "").strip() or None
        agent_id = str(workspace.get("agentId") or "").strip() or None

        payload: dict[str, Any] = {
            "topic": topic,
            "resolved": True,
            "source": "capabilities" if is_capability else "identity",
            "agentId": agent_id,
            "agentName": agent_name,
        }

        metadata["helpSelfHelp"] = payload

        logger.info(
            "self_help_requested topic=%s source=%s user_agent=%s",
            topic,
            payload["source"],
            agent_name or "common",
        )

    @classmethod
    def _resolve_topic(
        cls,
        *,
        message: str,
        identity_category: str | None,
        is_capability: bool,
    ) -> str:
        from app.application.services.chat_capabilities_service import (
            ChatCapabilitiesService,
        )

        if is_capability:
            if ChatCapabilitiesService.is_help_about_topic_inquiry(message):
                token = ChatCapabilitiesService.extract_help_about_topic(message)

                if token:
                    return token.replace(" ", "_")[:48]

            topic = ChatCapabilitiesService.classify_help_topic(message)

            if topic:
                return topic

            if ChatCapabilitiesService.is_release_notes_question(message):
                return "release_notes"

            if ChatCapabilitiesService.is_capabilities_question(message):
                return "capabilities_overview"

            return "capability_inquiry"

        return str(identity_category or "identity").strip() or "general"
