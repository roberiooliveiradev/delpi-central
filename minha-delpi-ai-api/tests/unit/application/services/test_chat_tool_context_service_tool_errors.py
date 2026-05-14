from app.application.services.chat_tool_context_service import ChatToolContextService


class FakeToolSelectionService:
    def select_tools(self, message):
        return [
            {
                "name": "execute_external_action",
                "reason": "consulta operacional",
                "arguments": {
                    "actionId": "buscar-produto",
                    "parameters": {
                        "message": "use a tabela de produtos",
                    },
                },
            }
        ]


class FakeExecuteToolUseCase:
    def execute(self, request):
        raise ValueError("Unknown parameter: message")


def test_build_context_keeps_stream_alive_when_tool_fails():
    service = ChatToolContextService(
        tool_selection_service=FakeToolSelectionService(),
        execute_tool_use_case=FakeExecuteToolUseCase(),
        external_action_selection_service=None,
    )

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="use a tabela de produtos",
        allowed_action_ids=["buscar-produto"],
        actions_enabled=True,
    )

    assert len(result["toolCalls"]) == 1
    assert result["toolCalls"][0]["name"] == "execute_external_action"
    assert result["toolCalls"][0]["metadata"]["ok"] is False
    assert result["toolCalls"][0]["metadata"]["error"] == "Unknown parameter: message"

    assert "Ferramenta autorizada com erro" in result["context"]
    assert "não invente o resultado" in result["context"]
    assert "Unknown parameter: message" in result["context"]
