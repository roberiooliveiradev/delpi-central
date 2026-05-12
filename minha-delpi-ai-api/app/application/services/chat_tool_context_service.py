import json

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.use_cases.execute_tool_use_case import ExecuteToolUseCase
from app.domain.services.tool_selection_service import ToolSelectionService
from app.infrastructure.config.settings import Settings


class ChatToolContextService:
    def __init__(
        self,
        tool_selection_service: ToolSelectionService,
        execute_tool_use_case: ExecuteToolUseCase,
        external_action_selection_service=None,
    ):
        self.tool_selection_service = tool_selection_service
        self.execute_tool_use_case = execute_tool_use_case
        self.external_action_selection_service = external_action_selection_service

    def build_context(
        self,
        user_id: str,
        access_token: str,
        message: str,
    ) -> dict:
        selected_tools = self.tool_selection_service.select_tools(message)

        if self.external_action_selection_service:
            selected_external_action = self.external_action_selection_service.select_action(message)

            if selected_external_action:
                selected_tools.append(selected_external_action)

        if not selected_tools:
            return {
                "context": "",
                "toolCalls": [],
            }

        context_blocks: list[str] = []
        safe_tool_calls: list[dict] = []

        for selected_tool in selected_tools:
            result = self.execute_tool_use_case.execute(
                ExecuteToolRequest(
                    user_id=user_id,
                    access_token=access_token,
                    tool_name=selected_tool["name"],
                    arguments=selected_tool.get("arguments") or {},
                )
            )

            # Safe metadata returned to the client and persisted in chat metadata.
            # Do not include raw tool data here. Raw data may contain user profile,
            # e-mail, permissions or operational values.
            safe_tool_calls.append(
                {
                    "name": result.name,
                    "arguments": selected_tool.get("arguments") or {},
                    "reason": selected_tool.get("reason"),
                    "metadata": result.metadata,
                }
            )

            # Authorized data is only injected into the LLM context for this request.
            # It is not returned in toolCalls[] and is not persisted in chat metadata.
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
            "toolCalls": safe_tool_calls,
        }

    def _format_tool_context(
        self,
        name: str,
        reason: str | None,
        data,
        metadata: dict | None,
    ) -> str:
        payload = {
            "tool": name,
            "reason": reason,
            "metadata": metadata or {},
            "authorizedResult": data,
        }

        return (
            f"[Ferramenta autorizada: {name}]\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
        )
