from dataclasses import dataclass

from app.application.services.chat_tool_context_service import ChatToolContextService
from app.domain.entities.tool_result import ToolResult
from app.domain.services.tool_selection_service import ToolSelectionService


@dataclass
class _RecoveryExecuteToolUseCase:
    calls: int = 0

    def execute(self, request):
        self.calls += 1
        return ToolResult(
            name="execute_external_action",
            data={"data": {"items": [{"branch": "01", "qty": 10}]}},
            metadata={
                "ok": True,
                "actionId": request.arguments.get("actionId"),
                "path": "/products/10080077/stock",
            },
        )


class _BlockedSelectionService:
    def select_action(self, *args, **kwargs):
        return {
            "name": "execute_external_action",
            "arguments": {"actionId": "wrong-action", "parameters": {}},
            "reason": "não deve ser chamado",
        }


def test_build_context_error_recovery_retries_failed_action():
    execute_tool = _RecoveryExecuteToolUseCase()
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=execute_tool,
        external_action_selection_service=_BlockedSelectionService(),
    )
    previous_messages = [
        {
            "role": "assistant",
            "metadata": {
                "errorHandling": {"type": "api_unavailable"},
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "stock-action",
                            "parameters": {"productCode": "10080077"},
                        },
                        "metadata": {
                            "ok": False,
                            "statusCode": 503,
                            "actionId": "stock-action",
                            "path": "/products/10080077/stock",
                        },
                    }
                ],
            },
        }
    ]

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="tente novamente a consulta anterior",
        previous_messages=previous_messages,
        allowed_action_ids=["stock-action", "wrong-action"],
    )

    assert execute_tool.calls == 1
    assert result.get("skipRag") is True
    metadata = result["toolCalls"][0]["metadata"]
    assert metadata.get("ok") is True
    assert metadata.get("errorRecoveryAttempt", {}).get("strategy") == "retry_last"
