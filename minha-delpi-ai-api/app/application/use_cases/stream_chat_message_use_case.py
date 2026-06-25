from collections.abc import Iterator

from app.application.dto.send_chat_message_request import SendChatMessageRequest
from app.application.services.chat_message_security_service import ChatMessageSecurityService
from app.application.services.chat_prompt_builder_service import ChatPromptBuilderService
from app.application.services.chat_tool_context_service import ChatToolContextService
from app.application.services.chat_workspace_context_service import ChatWorkspaceContextService
from app.application.services.rag_context_service import RagContextService
from app.application.services.chat_turn.chat_turn_completion_service import (
    ChatTurnCompletionService,
)
from app.application.services.chat_turn.chat_turn_preparation_service import (
    ChatTurnPreparationService,
)
from app.application.services.chat_turn.chat_turn_use_case_support_service import (
    ChatTurnUseCaseSupportService,
)
from app.application.services.chat_turn.chat_stream_session_title_service import (
    ChatStreamSessionTitleService,
)
from app.application.services.chat_turn.chat_stream_turn_execution_service import (
    ChatStreamTurnExecutionDeps,
    ChatStreamTurnExecutionService,
)
from app.application.services.chat_turn.chat_stream_turn_prepare_service import (
    ChatStreamTurnPrepareService,
)
from app.application.services.chat_web_search_synthesis_service import (
    ChatWebSearchSynthesisService,
)
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.chat_agent_repository_port import ChatAgentRepositoryPort
from app.domain.ports.chat_attachment_repository_port import ChatAttachmentRepositoryPort
from app.domain.ports.chat_session_repository_port import ChatSessionRepositoryPort
from app.domain.ports.llm_gateway_port import LlmGatewayPort
from app.domain.services.prompt_policy_service import PromptPolicyService
from app.application.services.chat_llm_metadata_service import ChatLlmMetadataService
from app.infrastructure.config.settings import Settings  # noqa: F401 — patches de teste legados
from app.infrastructure.llm.llm_request_context import llm_generation_scope


class StreamChatMessageUseCase:
    def __init__(
        self,
        chat_repository: ChatSessionRepositoryPort,
        audit_repository: AuditRepositoryPort,
        llm_gateway: LlmGatewayPort,
        prompt_policy_service: PromptPolicyService,
        rag_context_service: RagContextService,
        chat_tool_context_service: ChatToolContextService,
        agent_repository: ChatAgentRepositoryPort | None = None,
        attachment_repository: ChatAttachmentRepositoryPort | None = None,
        chat_attachment_context_service=None,
        chat_history_summary_service=None,
        chat_agentic_tool_loop_service=None,
        workspace_context_service: ChatWorkspaceContextService | None = None,
        admin_guideline_prompt_service=None,
        message_security_service: ChatMessageSecurityService | None = None,
        web_search_synthesis_service: ChatWebSearchSynthesisService | None = None,
        session_memory_service=None,
        turn_completion_service: ChatTurnCompletionService | None = None,
    ):
        self.chat_repository = chat_repository
        self.llm_gateway = llm_gateway
        self.message_security_service = message_security_service or ChatMessageSecurityService(
            audit_repository=audit_repository,
        )
        self.prompt_builder_service = ChatPromptBuilderService(prompt_policy_service)
        self.turn_preparation_service = ChatTurnPreparationService(
            rag_context_service=rag_context_service,
            session_memory_service=session_memory_service,
        )
        self.turn_completion_service = turn_completion_service or ChatTurnCompletionService(
            chat_repository=chat_repository,
            audit_repository=audit_repository,
            session_memory_service=session_memory_service,
        )
        self.web_search_synthesis_service = (
            web_search_synthesis_service
            or ChatWebSearchSynthesisService(llm_gateway=llm_gateway)
        )
        self.turn_support = ChatTurnUseCaseSupportService(
            agent_repository=agent_repository,
            attachment_repository=attachment_repository,
            chat_attachment_context_service=chat_attachment_context_service,
            chat_history_summary_service=chat_history_summary_service,
            chat_agentic_tool_loop_service=chat_agentic_tool_loop_service,
            workspace_context_service=workspace_context_service,
            admin_guideline_prompt_service=admin_guideline_prompt_service,
            chat_tool_context_service=chat_tool_context_service,
        )
        self.session_title_service = ChatStreamSessionTitleService()
        self.stream_prepare = ChatStreamTurnPrepareService(
            chat_repository=chat_repository,
            turn_preparation_service=self.turn_preparation_service,
            turn_support=self.turn_support,
            session_title_service=self.session_title_service,
        )
        self._stream_deps = ChatStreamTurnExecutionDeps(
            chat_repository=self.chat_repository,
            message_security_service=self.message_security_service,
            turn_support=self.turn_support,
            session_title_service=self.session_title_service,
            stream_prepare=self.stream_prepare,
            prompt_builder_service=self.prompt_builder_service,
            llm_gateway=self.llm_gateway,
            web_search_synthesis_service=self.web_search_synthesis_service,
            turn_completion_service=self.turn_completion_service,
        )

    def stream(self, request: SendChatMessageRequest) -> Iterator[dict]:
        generation_config = ChatLlmMetadataService.resolve_generation_config(request)

        with llm_generation_scope(generation_config):
            yield from ChatStreamTurnExecutionService.iter_turn(request, self._stream_deps)
