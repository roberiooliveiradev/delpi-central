from app.application.security.chat_permissions import CHAT_ASK_PERMISSION
from app.domain.entities.tool_result import ToolResult
from app.domain.exceptions.tool_exceptions import InvalidToolInputError
from app.domain.ports.internal_tool_port import InternalToolPort
from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService
from app.domain.services.web_search_portuguese_content_service import (
    WebSearchPortugueseContentService,
)
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

        planned_raw = arguments.get("plannedQueries")
        planned_queries = (
            [str(item).strip() for item in planned_raw if str(item).strip()]
            if isinstance(planned_raw, list)
            else None
        )
        search_mode = str(arguments.get("searchMode") or "").strip() or None
        prefer_official = arguments.get("preferOfficial")

        payload = self.gateway.search(
            query,
            max_results=limit,
            planned_queries=planned_queries,
            search_mode=search_mode,
            prefer_official=prefer_official if prefer_official is not None else None,
        )
        payload = WebSearchPortugueseContentService.localize_payload(payload) or payload

        search_intent = str(arguments.get("searchIntent") or "").strip()

        if search_intent:
            payload["searchIntent"] = search_intent

        return ToolResult(
            name=self.name,
            data=payload,
            metadata={
                "source": "web_search",
                "provider": payload.get("provider"),
                "searchStatus": payload.get("searchStatus"),
                "count": len(payload.get("results") or []),
                "limit": limit,
                "searchMode": search_mode,
                "preferOfficial": prefer_official,
                "searchIntent": search_intent or None,
            },
        )
