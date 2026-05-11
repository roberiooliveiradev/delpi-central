from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.services.tool_selection_service import ToolSelectionService
from app.infrastructure.config.settings import Settings


class ChatToolContextService:
    def __init__(
        self,
        tool_selection_service: ToolSelectionService,
        execute_tool_use_case: ExecuteToolUseCase,
    ):
        self.tool_selection_service = tool_selection_service
        self.execute_tool_use_case = execute_tool_use_case

    def build_context(
        self,
        user_id: str,
        access_token: str,
        message: str,
    ) -> dict:
        selected_tools = self.tool_selection_service.select_tools(message)

        if not selected_tools:
            return {
                "context": "",
                "toolCalls": [],
            }

        context_blocks: list[str] = []
        tool_calls: list[dict] = []

        for selected_tool in selected_tools:
            result = self.execute_tool_use_case.execute(
                ExecuteToolRequest(
                    user_id=user_id,
                    access_token=access_token,
                    tool_name=selected_tool["name"],
                    arguments=selected_tool.get("arguments") or {},
                )
            )

            tool_call = {
                "name": result.name,
                "arguments": selected_tool.get("arguments") or {},
                "reason": selected_tool.get("reason"),
                "metadata": result.metadata,
                "data": result.data,
            }

            tool_calls.append(tool_call)

            context_blocks.append(
                self._format_tool_context(
                    name=result.name,
                    reason=selected_tool.get("reason"),
                    data=result.data,
                    metadata=result.metadata,
                )
            )

        context = "\n\n".join(context_blocks)
        context = context[: Settings.MAX_CONTEXT_CHARS]

        return {
            "context": context,
            "toolCalls": tool_calls,
        }

    def _format_tool_context(
        self,
        name: str,
        reason: str | None,
        data,
        metadata: dict | None,
    ) -> str:
        return (
            f"[Ferramenta: {name}]\n"
            f"Motivo: {reason or 'não informado'}\n"
            f"Metadados: {metadata or {}}\n"
            f"Resultado autorizado: {data}"
        )
