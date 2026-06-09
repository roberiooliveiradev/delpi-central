"""Helpers compartilhados entre SendChatMessageUseCase e StreamChatMessageUseCase."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable
from uuid import UUID

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_capabilities_service import ChatCapabilitiesService
from app.application.services.chat_user_context_service import ChatUserContextService
from app.infrastructure.config.settings import Settings

if TYPE_CHECKING:
    from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
    from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort


class ChatTurnUseCaseSupportService:
    def __init__(
        self,
        *,
        agent_repository: ChatAgentRepositoryPort | None = None,
        attachment_repository: ChatAttachmentRepositoryPort | None = None,
        chat_attachment_context_service=None,
        chat_history_summary_service=None,
        chat_agentic_tool_loop_service=None,
        workspace_context_service=None,
        admin_guideline_prompt_service=None,
        chat_tool_context_service=None,
    ) -> None:
        self.agent_repository = agent_repository
        self.attachment_repository = attachment_repository
        self.chat_attachment_context_service = chat_attachment_context_service
        self.chat_history_summary_service = chat_history_summary_service
        self.chat_agentic_tool_loop_service = chat_agentic_tool_loop_service
        self.workspace_context_service = workspace_context_service
        self.admin_guideline_prompt_service = admin_guideline_prompt_service
        self.chat_tool_context_service = chat_tool_context_service

    @staticmethod
    def guideline_metadata(guidelines: list[dict]) -> list[dict]:
        return [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "category": item.get("category"),
                "status": item.get("status"),
            }
            for item in guidelines
        ]

    @staticmethod
    def embedding_cache_stats() -> dict | None:
        try:
            from app.composition.external_action_composer import get_embedding_cache_stats

            return get_embedding_cache_stats()
        except Exception:
            return None

    def build_admin_guidelines_prompt(self, workspace_context: dict) -> tuple[str, list[dict]]:
        if not self.admin_guideline_prompt_service:
            return "", []

        specialization = workspace_context.get("specialization") or {}
        categories = specialization.get("guidelineCategories")

        return self.admin_guideline_prompt_service.build_active_guidelines_prompt(
            categories=categories,
        )

    def get_message_attachments(
        self,
        request: SendChatMessageRequest,
        user_id: UUID,
        session_id: UUID,
    ) -> list[dict]:
        if not self.attachment_repository or not request.attachment_ids:
            return []

        attachment_ids = [UUID(value) for value in request.attachment_ids]

        attachments = self.attachment_repository.list_attachments_by_ids(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

        return [
            {
                "id": str(attachment.id),
                "filename": attachment.filename,
                "original_filename": attachment.original_filename,
                "content_type": attachment.content_type,
                "size_bytes": attachment.size_bytes,
                "status": attachment.status,
                "metadata": attachment.metadata,
            }
            for attachment in attachments
        ]

    def attach_files_to_message(
        self,
        *,
        request: SendChatMessageRequest,
        user_id: UUID,
        session_id: UUID,
        message_id: UUID,
    ) -> None:
        if not self.attachment_repository or not request.attachment_ids:
            return

        attachment_ids = [UUID(value) for value in request.attachment_ids]

        self.attachment_repository.attach_to_message(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
            message_id=message_id,
        )

    def build_attachment_context(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        request: SendChatMessageRequest,
    ) -> str:
        if not self.chat_attachment_context_service or not request.attachment_ids:
            return ""

        attachment_ids = [UUID(value) for value in request.attachment_ids]

        return self.chat_attachment_context_service.build_context(
            user_id=user_id,
            session_id=session_id,
            attachment_ids=attachment_ids,
        )

    def prepare_history(self, previous_messages) -> tuple[str, list]:
        if self.chat_history_summary_service:
            return self.chat_history_summary_service.prepare_history(previous_messages)

        keep = Settings.CHAT_HISTORY_MAX_MESSAGES

        return "", list(previous_messages[-keep:])

    def build_workspace_context(
        self,
        session,
        user_id: UUID,
        *,
        request_agent_id: str | None = None,
        supplemental_agent_ids: list[str] | None = None,
        supplemental_project_ids: list[str] | None = None,
    ) -> dict:
        if self.workspace_context_service:
            return self.workspace_context_service.build_context(
                session=session,
                user_id=user_id,
                request_agent_id=request_agent_id,
                supplemental_agent_ids=supplemental_agent_ids,
                supplemental_project_ids=supplemental_project_ids,
            )

        agent = self._get_session_agent(session, user_id)

        from app.application.services.chat_agent_skills_service import ChatAgentSkillsService

        return {
            "project": None,
            "agent": self._agent_metadata(agent),
            "projectPrompt": None,
            "agentPrompt": agent.system_prompt if agent else None,
            "agentId": str(agent.id) if agent else (str(session.agent_id) if session.agent_id else None),
            "allowedActionIds": [],
            "actionsEnabled": False,
            "userActivatedAgent": bool(session.agent_id or request_agent_id),
            "capabilities": {},
            "skills": ChatAgentSkillsService.resolve(
                agent_metadata=agent.metadata if agent else {},
                allowed_action_ids=[],
                has_agent=bool(agent),
            ),
            "specialization": None,
        }

    def _get_session_agent(self, session, user_id: UUID):
        if not self.agent_repository or not session.agent_id:
            return None

        return self.agent_repository.get_enabled_by_id(
            session.agent_id,
            user_id=user_id,
        )

    @staticmethod
    def _agent_metadata(agent) -> dict | None:
        if not agent:
            return None

        return {
            "id": str(agent.id),
            "name": agent.name,
            "description": agent.description,
            "metadata": agent.metadata,
        }

    def resolve_llm_user_context(
        self,
        access_token: str | None,
        message: str,
        *,
        operational_optimize: bool,
        analysis_mode: bool = False,
    ) -> str | None:
        if analysis_mode and not ChatUserContextService.is_user_identity_question(message):
            return None

        if (
            operational_optimize
            and Settings.CHAT_OPERATIONAL_SLIM_USER_CONTEXT
            and not ChatUserContextService.is_user_identity_question(message)
        ):
            return None

        block = self.build_user_context(access_token)
        return block or None

    @staticmethod
    def build_user_context(access_token: str | None) -> str:
        if not access_token:
            return ""

        from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway

        service = ChatUserContextService(core_api_gateway=CoreApiHttpGateway())
        return service.build_user_context(access_token)

    @staticmethod
    def resolve_user_identity_answer(access_token: str | None, message: str) -> str | None:
        if not access_token:
            return None

        from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway

        service = ChatUserContextService(core_api_gateway=CoreApiHttpGateway())
        return service.build_direct_answer(access_token, message)

    @staticmethod
    def resolve_capabilities_answer(
        workspace_context: dict,
        message: str,
    ) -> str | None:
        allowed = workspace_context.get("allowedActionIds") or []
        catalog = ChatCapabilitiesService.load_action_catalog_for_agent(allowed)
        return ChatCapabilitiesService.resolve_capability_answer(
            message=message,
            workspace_context=workspace_context,
            allowed_action_ids=allowed,
            action_catalog=catalog,
        )

    def maybe_extend_tool_context(
        self,
        *,
        request: SendChatMessageRequest,
        workspace_context: dict,
        tool_context: dict,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        on_stream_activity: Callable | None = None,
    ) -> dict:
        from app.application.services.chat_small_talk_service import ChatSmallTalkService

        if ChatSmallTalkService.is_small_talk(request.message):
            return tool_context

        from app.application.services.chat_utility_direct_answer_service import (
            ChatUtilityDirectAnswerService,
        )

        if ChatUtilityDirectAnswerService.is_utility_question(request.message):
            return tool_context

        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(request.message):
            return tool_context

        if not self.chat_agentic_tool_loop_service or not request.access_token:
            return tool_context

        from app.application.services.chat_workspace_agent_activation_service import (
            ChatWorkspaceAgentActivationService,
        )

        if not ChatWorkspaceAgentActivationService.operational_tools_enabled(
            workspace_context
        ):
            return tool_context

        specialization = workspace_context.get("specialization") or {}
        allowed_tool_names = None

        if isinstance(specialization, dict):
            allowed_tool_names = specialization.get("allowedTools")

        if on_stream_activity:
            from app.application.services.chat_stream_activity_service import (
                ChatStreamActivityService,
            )

            on_stream_activity(
                ChatStreamActivityService.think(
                    target="passos adicionais (agentic)",
                    message="Verificando se preciso de mais alguma informação...",
                    detail="Verificando se ainda faltam ferramentas para responder.",
                )
            )

        return self.chat_agentic_tool_loop_service.extend_tool_context(
            user_id=request.user_id,
            access_token=request.access_token,
            message=request.message,
            tool_context=tool_context,
            allowed_tool_names=allowed_tool_names,
            allowed_action_ids=workspace_context.get("allowedActionIds"),
            conversation_context=conversation_context,
            previous_messages=previous_messages,
            on_stream_activity=on_stream_activity,
        )

    def build_tool_context(
        self,
        request: SendChatMessageRequest,
        *,
        allowed_action_ids: list[str] | None = None,
        capabilities: dict | None = None,
        specialization: dict | None = None,
        fast_path: bool = False,
        previous_messages: list | None = None,
        max_external_action_calls: int | None = None,
        on_stream_activity: Callable | None = None,
        agent_context: dict | None = None,
        working_memory: dict | None = None,
    ) -> dict:
        if not request.access_token:
            return {
                "context": "",
                "toolCalls": [],
            }

        actions_enabled = True

        if capabilities and capabilities.get("actions") is False:
            actions_enabled = False

        allowed_tool_names = None

        if isinstance(specialization, dict):
            allowed_tool_names = specialization.get("allowedTools")

        return self.chat_tool_context_service.build_context(
            user_id=request.user_id,
            access_token=request.access_token,
            message=request.message,
            allowed_action_ids=allowed_action_ids,
            actions_enabled=actions_enabled,
            allowed_tool_names=allowed_tool_names,
            fast_path=fast_path,
            previous_messages=previous_messages,
            max_external_action_calls=max_external_action_calls,
            on_stream_activity=on_stream_activity,
            agent_context=agent_context,
            working_memory=working_memory,
            attachment_context=self.build_attachment_context(
                user_id=UUID(request.user_id),
                session_id=UUID(request.session_id),
                request=request,
            ),
            attachment_ids=getattr(request, "attachment_ids", None),
            session_id=str(request.session_id) if getattr(request, "session_id", None) else None,
        )

    def run_post_rag_web_fallback(
        self,
        request: SendChatMessageRequest,
        *,
        previous_messages: list | None = None,
        on_stream_activity: Callable | None = None,
    ) -> dict | None:
        if not request.access_token or not self.chat_tool_context_service:
            return None

        return self.chat_tool_context_service.run_post_rag_web_fallback(
            user_id=request.user_id,
            access_token=request.access_token,
            message=request.message,
            previous_messages=previous_messages,
            on_stream_activity=on_stream_activity,
        )
