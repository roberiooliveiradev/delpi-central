from app.infrastructure.tools.execute_external_action_tool import ExecuteExternalActionTool
from app.composition.external_action_composer import make_postgres_external_action_repository
from app.infrastructure.external_actions.http_external_action_gateway import HttpExternalActionGateway
from app.domain.services.external_actions.external_action_execution_policy import ExternalActionExecutionPolicy
from app.application.use_cases.execute_external_action_use_case import ExecuteExternalActionUseCase
from app.application.services.permission_context_service import PermissionContextService
from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.domain.services.tool_policy_service import ToolPolicyService
from app.infrastructure.embeddings.local_embedding_gateway import LocalEmbeddingGateway
from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository
from app.infrastructure.persistence.postgres_knowledge_repository import (
    PostgresKnowledgeRepository,
)
from app.infrastructure.tools.get_allowed_apps_tool import GetAllowedAppsTool
from app.infrastructure.tools.get_allowed_routes_tool import GetAllowedRoutesTool
from app.infrastructure.tools.get_current_user_tool import GetCurrentUserTool
from app.infrastructure.tools.search_knowledge_base_tool import SearchKnowledgeBaseTool


def make_execute_tool_use_case() -> ExecuteToolUseCase:
    core_api_gateway = CoreApiHttpGateway()

    search_knowledge_use_case = SearchKnowledgeUseCase(
        knowledge_repository=PostgresKnowledgeRepository(),
        embedding_gateway=LocalEmbeddingGateway(),
    )

    execute_external_action_use_case = ExecuteExternalActionUseCase(
        repository=make_postgres_external_action_repository(),
        gateway=HttpExternalActionGateway(),
        policy=ExternalActionExecutionPolicy(),
        audit_repository=PostgresAuditRepository(),
    )

    tools = {
        "get_current_user": GetCurrentUserTool(core_api_gateway),
        "get_allowed_apps": GetAllowedAppsTool(core_api_gateway),
        "get_allowed_routes": GetAllowedRoutesTool(core_api_gateway),
        "search_knowledge_base": SearchKnowledgeBaseTool(search_knowledge_use_case),
        "execute_external_action": ExecuteExternalActionTool(execute_external_action_use_case),
    }

    return ExecuteToolUseCase(
        tools=tools,
        permission_context_service=PermissionContextService(core_api_gateway),
        tool_policy_service=ToolPolicyService(),
        audit_repository=PostgresAuditRepository(),
    )
