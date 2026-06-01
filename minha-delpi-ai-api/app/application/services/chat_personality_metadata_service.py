"""Anexa tom contextual (follow-ups, risco) ao metadata da resposta."""

from __future__ import annotations

from app.application.services.chat_follow_up_suggestion_service import (
    ChatFollowUpSuggestionService,
)
from app.domain.services.chat_agent_personality_service import ChatAgentPersonalityService
from app.domain.services.chat_agent_profile_service import ChatAgentProfileService


class ChatPersonalityMetadataService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str,
        answer: str,
        tool_calls: list | None,
        workspace_context: dict | None,
        issues: list[str] | None = None,
        previous_messages: list | None = None,
        attachments: list[dict] | None = None,
        latency_ms: int | None = None,
    ) -> None:
        profile = ChatAgentProfileService.from_workspace(workspace_context)
        personality = ChatAgentPersonalityService.from_profile(profile)
        risk_level = ChatFollowUpSuggestionService.assess_risk_level(
            answer=answer,
            tool_calls=tool_calls or [],
            issues=issues,
        )

        metadata["personality"] = {
            "tone": personality.tone,
            "humorLevel": ChatAgentPersonalityService.effective_humor_level(
                personality,
                risk_level=risk_level,
            ),
            "emojiLevel": personality.emoji_level if risk_level < 2 else 0,
            "proactivity": personality.proactivity,
            "suggestFollowUps": personality.suggest_follow_ups,
            "riskLevel": risk_level,
        }

        ChatFollowUpSuggestionService.attach_to_assistant_metadata(
            metadata,
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            workspace_context=workspace_context,
            issues=issues,
            previous_messages=previous_messages,
        )

        from app.application.services.chat_trust_metadata_service import (
            ChatTrustMetadataService,
        )

        ChatTrustMetadataService.attach_to_assistant_metadata(
            metadata,
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            sources=metadata.get("sources") if isinstance(metadata.get("sources"), list) else None,
            workspace_context=workspace_context,
            direct_response=bool(metadata.get("directResponse")),
        )

        from app.application.services.chat_error_handling_service import (
            ChatErrorHandlingService,
        )
        from app.application.services.chat_help_error_follow_up_service import (
            ChatHelpErrorFollowUpService,
        )

        enriched_workspace = dict(workspace_context or {})

        if previous_messages is not None:
            enriched_workspace["previousMessages"] = previous_messages

        ChatErrorHandlingService.attach_to_assistant_metadata(
            metadata,
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            issues=issues,
            workspace_context=enriched_workspace,
            attachments=attachments,
            latency_ms=latency_ms,
        )

        ChatHelpErrorFollowUpService.attach_to_assistant_metadata(
            metadata,
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            issues=issues,
            workspace_context=workspace_context,
        )

        from app.application.services.chat_action_confirmation_metadata_service import (
            ChatActionConfirmationMetadataService,
        )

        ChatActionConfirmationMetadataService.attach_to_assistant_metadata(
            metadata,
            tool_calls=tool_calls,
            user_message=message,
        )
