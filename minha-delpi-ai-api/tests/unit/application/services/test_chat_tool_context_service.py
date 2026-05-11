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


class FakeExecuteToolUseCase:
    def execute(self, request):
        return ToolResult(
            name="get_current_user",
            data={
                "id": "user-1",
                "name": "Usuário Teste",
                "email": "teste@delpi.com.br",
                "isSuperadmin": True,
            },
            metadata={
                "source": "core-api:/me",
            },
        )


def test_tool_data_is_in_context_but_not_in_tool_calls():
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=FakeExecuteToolUseCase(),
    )

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="Quem sou eu?",
    )

    assert "teste@delpi.com.br" in result["context"]
    assert result["toolCalls"][0]["name"] == "get_current_user"
    assert "data" not in result["toolCalls"][0]
