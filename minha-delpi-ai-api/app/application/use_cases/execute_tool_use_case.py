from uuid import UUID

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.dto.execute_tool_response import ExecuteToolResponse
from app.application.services.permission_context_service import PermissionContextService
from app.domain.exceptions.tool_exceptions import ToolNotFoundError
from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.internal_tool_port import InternalToolPort
from app.domain.services.tool_policy_service import ToolPolicyService


class ExecuteToolUseCase:
    def __init__(
        self,
        tools: dict[str, InternalToolPort],
        permission_context_service: PermissionContextService,
        tool_policy_service: ToolPolicyService,
        audit_repository: AuditRepositoryPort,
    ):
        self.tools = tools
        self.permission_context_service = permission_context_service
        self.tool_policy_service = tool_policy_service
        self.audit_repository = audit_repository

    def execute(self, request: ExecuteToolRequest) -> ExecuteToolResponse:
        tool = self.tools.get(request.tool_name)

        if not tool:
            raise ToolNotFoundError(request.tool_name)

        permission_context = self.permission_context_service.load_context(
            request.access_token
        )

        self.tool_policy_service.require_tool_permission(
            tool_name=tool.name,
            required_permission=tool.required_permission,
            permission_context=permission_context,
        )

        tool_arguments = {
            **(request.arguments or {}),
            "_userId": request.user_id,
        }

        result = tool.execute(
            arguments=tool_arguments,
            access_token=request.access_token,
        )

        sanitized_data = self.tool_policy_service.sanitize_for_llm(result.data)

        self.audit_repository.log(
            user_id=UUID(request.user_id),
            action="chat.tool.called",
            context="tool",
            tool_calls=[
                {
                    "name": tool.name,
                    "requiredPermission": tool.required_permission,
                    "metadata": result.metadata,
                }
            ],
            metadata={
                "tool": tool.name,
                "required_permission": tool.required_permission,
            },
        )

        return ExecuteToolResponse(
            name=result.name,
            data=sanitized_data,
            metadata=result.metadata,
        )
