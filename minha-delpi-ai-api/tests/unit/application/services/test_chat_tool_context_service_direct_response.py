from dataclasses import dataclass

from app.application.services.chat_tool_context_service import ChatToolContextService
from app.domain.entities.tool_result import ToolResult
from app.domain.services.tool_selection_service import ToolSelectionService


@dataclass
class FakeExecuteToolRequest:
    user_id: str
    access_token: str
    tool_name: str
    arguments: dict


class FakeExternalActionExecuteToolUseCase:
    def execute(self, request):
        return ToolResult(
            name="execute_external_action",
            data={
                "success": True,
                "data": {
                    "product": {
                        "code": "10080055",
                        "description": "TERM. FASTON 4,80X0,50",
                        "type": "ME",
                        "unit": "UN",
                        "group_code": "1008",
                        "active": True,
                    }
                },
            },
            metadata={
                "ok": True,
                "statusCode": 200,
                "actionId": "action-1",
                "path": "/products/{code}/analyser",
                "provider": "api_delpi",
            },
        )


class FakeExternalActionSelectionService:
    def select_action(self, message, allowed_action_ids=None):
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": "action-1",
                "parameters": {"code": "10080055"},
            },
            "reason": "Consulta de produto",
        }


def test_build_context_sets_direct_answer_for_successful_external_action():
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=FakeExternalActionExecuteToolUseCase(),
        external_action_selection_service=FakeExternalActionSelectionService(),
    )

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="descrição do produto 10080055",
        allowed_action_ids=["action-1"],
    )

    assert result["skipRag"] is True
    assert "10080055" in result["directAnswer"]
    assert "TERM. FASTON" in result["directAnswer"]
    assert len(result["toolCalls"]) == 1
