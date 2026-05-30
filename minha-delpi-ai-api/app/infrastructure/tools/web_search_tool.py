from app.application.security.chat_permissions import CHAT_ASK_PERMISSION
from app.domain.entities.tool_result import ToolResult
from app.domain.exceptions.tool_exceptions import InvalidToolInputError
from app.domain.ports.internal_tool_port import InternalToolPort
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService
from app.infrastructure.config.settings import Settings
from app.infrastructure.gateways.web_search_http_gateway import WebSearchHttpGateway


class WebSearchTool(InternalToolPort):
    name = "web_search"
    description = (
        "Pesquisa informações públicas na internet quando autorizado. "
        "Use apenas para fatos externos à plataforma DELPI; cite fontes retornadas."
    )
    required_permission = CHAT_ASK_PERMISSION

    def __init__(self, gateway: WebSearchHttpGateway | None = None):
        self.gateway = gateway or WebSearchHttpGateway()

    def execute(self, arguments: dict, access_token: str) -> ToolResult:
        if not ChatWebSearchIntentService.is_feature_enabled():
            raise InvalidToolInputError("web_search is disabled")

        query = str(arguments.get("query") or "").strip()

        if not query:
            raise InvalidToolInputError("query is required")

        raw_limit = arguments.get("limit", Settings.CHAT_WEB_SEARCH_MAX_RESULTS)

        try:
            limit = int(raw_limit)
        except (TypeError, ValueError) as exc:
            raise InvalidToolInputError("limit must be an integer") from exc

        limit = max(1, min(limit, Settings.CHAT_WEB_SEARCH_MAX_RESULTS))

        payload = self.gateway.search(query, max_results=limit)

        return ToolResult(
            name=self.name,
            data=payload,
            metadata={
                "source": "web_search",
                "provider": payload.get("provider"),
                "searchStatus": payload.get("searchStatus"),
                "count": len(payload.get("results") or []),
                "limit": limit,
            },
        )
