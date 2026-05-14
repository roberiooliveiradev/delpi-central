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


class GetAllowedRoutesTool(InternalToolPort):
    name = "get_allowed_routes"
    description = "Lista rotas autorizadas ao usuário atual a partir dos apps permitidos."
    required_permission = CHAT_ACCESS_PERMISSION

    def __init__(self, core_api_gateway: CoreApiHttpGateway):
        self.core_api_gateway = core_api_gateway

    def execute(self, arguments: dict, access_token: str) -> ToolResult:
        apps = self.core_api_gateway.get_apps(access_token)

        routes = []

        for app in apps:
            for route in app.get("routes") or []:
                routes.append(
                    {
                        "appId": app.get("id"),
                        "appName": app.get("name"),
                        "path": route.get("path"),
                        "label": route.get("label"),
                        "permission": route.get("permission"),
                        "showInMenu": route.get("showInMenu"),
                    }
                )

        limited_routes = routes[:80]

        return ToolResult(
            name=self.name,
            data=limited_routes,
            metadata={
                "source": "core-api:/me/apps",
                "count": len(limited_routes),
                "truncated": len(routes) > len(limited_routes),
            },
        )
