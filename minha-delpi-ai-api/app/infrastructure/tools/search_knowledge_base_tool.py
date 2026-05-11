from app.application.dto.search_knowledge_request import SearchKnowledgeRequest
from app.application.use_cases.search_knowledge_use_case import SearchKnowledgeUseCase
from app.domain.entities.tool_result import ToolResult
from app.domain.exceptions.tool_exceptions import InvalidToolInputError
from app.domain.ports.internal_tool_port import InternalToolPort


class SearchKnowledgeBaseTool(InternalToolPort):
    name = "search_knowledge_base"
    description = "Busca trechos relevantes na base documental autorizada do Minha DELPI Chat."
    required_permission = "minha-delpi.chat.access"

    def __init__(self, search_knowledge_use_case: SearchKnowledgeUseCase):
        self.search_knowledge_use_case = search_knowledge_use_case

    def execute(self, arguments: dict, access_token: str) -> ToolResult:
        query = str(arguments.get("query") or "").strip()

        if not query:
            raise InvalidToolInputError("query is required")

        raw_limit = arguments.get("limit", 5)

        try:
            limit = int(raw_limit)
        except (TypeError, ValueError) as exc:
            raise InvalidToolInputError("limit must be an integer") from exc

        limit = max(1, min(limit, 5))

        results = self.search_knowledge_use_case.execute(
            SearchKnowledgeRequest(
                query=query,
                limit=limit,
            )
        )

        return ToolResult(
            name=self.name,
            data=results,
            metadata={
                "source": "ai_knowledge_chunks",
                "count": len(results),
                "limit": limit,
            },
        )
