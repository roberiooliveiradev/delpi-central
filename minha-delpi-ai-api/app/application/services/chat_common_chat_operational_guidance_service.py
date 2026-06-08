"""Orientação quando o chat comum recebe pedido que exige APIs/actions."""

from __future__ import annotations

from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_turn.chat_turn_preparation_content_service import (
    ChatTurnPreparationContentService,
)
from app.application.services.chat_workspace_agent_activation_service import (
    ChatWorkspaceAgentActivationService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_fast_path_service import ChatFastPathService
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
from app.domain.services.chat_technical_description_intent_service import (
    ChatTechnicalDescriptionIntentService,
)
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService


class ChatCommonChatOperationalGuidanceService:
    @classmethod
    def requires_agent(cls, message: str, *, workspace_context: dict | None) -> bool:
        if ChatWorkspaceAgentActivationService.operational_tools_enabled(
            workspace_context
        ):
            return False

        if not str(message or "").strip():
            return False

        if ChatFastPathService.is_small_talk(message):
            return False

        if ChatCapabilitiesService.is_capability_inquiry(message):
            return False

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(message):
            return False

        if ChatSqlIntentService.is_authoring_request(message):
            return False

        if ChatWebSearchIntentService.matches(message):
            return False

        return ChatCapabilitiesService.looks_like_operational_data_request(message)

    @classmethod
    def resolve_direct_answer(
        cls,
        message: str,
        *,
        workspace_context: dict | None,
        previous_messages: list | None = None,
    ) -> str | None:
        if not cls.requires_agent(message, workspace_context=workspace_context):
            return None

        if ChatAnalysisIntentService.is_data_interpretation_request(
            message,
            previous_messages,
        ):
            from app.application.services.chat_conversation_context_service import (
                ChatConversationContextService,
            )

            if ChatConversationContextService.has_recent_tool_data(previous_messages):
                return None

        return cls.build_direct_answer()

    @classmethod
    def build_direct_answer(cls) -> str:
        title = ChatTurnPreparationContentService.get(
            "directAnswers",
            "commonChatOperationalGuidance",
            "title",
        )
        intro = ChatTurnPreparationContentService.get(
            "directAnswers",
            "commonChatOperationalGuidance",
            "intro",
        )
        capabilities_title = ChatTurnPreparationContentService.get(
            "directAnswers",
            "commonChatOperationalGuidance",
            "commonChatCapabilitiesTitle",
        )
        agent_hint = ChatTurnPreparationContentService.get(
            "directAnswers",
            "commonChatOperationalGuidance",
            "agentHint",
        )
        items = ChatAssistantContentService.list(
            "turn_preparation",
            "directAnswers",
            "commonChatOperationalGuidance",
            "commonChatCapabilitiesItems",
        )

        lines: list[str] = []

        if title:
            lines.append(title)
            lines.append("")

        if intro:
            lines.append(intro)
            lines.append("")

        if capabilities_title:
            lines.append(capabilities_title)

        for item in items:
            lines.append(f"- {item}")

        if agent_hint:
            lines.append("")
            lines.append(agent_hint)

        return "\n".join(lines).strip()
