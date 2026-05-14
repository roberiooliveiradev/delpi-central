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


class GetAllowedAppsTool(InternalToolPort):
    name = "get_allowed_apps"
    description = "Lista apps autorizados ao usuário atual."
    required_permission = CHAT_ACCESS_PERMISSION

    def __init__(self, core_api_gateway: CoreApiHttpGateway):
        self.core_api_gateway = core_api_gateway

    def execute(self, arguments: dict, access_token: str) -> ToolResult:
        apps = self.core_api_gateway.get_apps(access_token)

        limited_apps = []

        for app in apps[:30]:
            routes = app.get("routes") or []

            limited_apps.append(
                {
                    "id": app.get("id"),
                    "name": app.get("name"),
                    "basePath": app.get("basePath"),
                    "type": app.get("type"),
                    "renderMode": app.get("renderMode"),
                    "routeCount": len(routes),
                }
            )

        return ToolResult(
            name=self.name,
            data=limited_apps,
            metadata={
                "source": "core-api:/me/apps",
                "count": len(limited_apps),
                "truncated": len(apps) > len(limited_apps),
            },
        )
