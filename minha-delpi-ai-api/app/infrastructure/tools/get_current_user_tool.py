from app.application.security.chat_permissions import (
    CHAT_ACCESS_PERMISSION,
    CHAT_ADMIN_PERMISSION,
    CHAT_ASK_PERMISSION,
    CHAT_HISTORY_VIEW_PERMISSION,
    CHAT_KNOWLEDGE_MANAGE_PERMISSION,
    CHAT_TOOLS_MANAGE_PERMISSION,
    CHAT_TOOLS_USE_PERMISSION,
)
from app.domain.entities.tool_result import ToolResult
from app.domain.ports.internal_tool_port import InternalToolPort
from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway


class GetCurrentUserTool(InternalToolPort):
    name = "get_current_user"
    description = "Retorna dados mínimos do usuário autenticado."
    required_permission = CHAT_ACCESS_PERMISSION

    def __init__(self, core_api_gateway: CoreApiHttpGateway):
        self.core_api_gateway = core_api_gateway

    def execute(self, arguments: dict, access_token: str) -> ToolResult:
        me = self.core_api_gateway.get_me(access_token)

        data = {
            "id": me.get("id"),
            "name": me.get("name"),
            "email": me.get("email"),
            "isSuperadmin": bool(me.get("is_superadmin", False)),
        }

        return ToolResult(
            name=self.name,
            data=data,
            metadata={
                "source": "core-api:/me",
            },
        )
