from app.application.services.chat_tool_context_service import ChatToolContextService


class FakeToolSelectionService:
    def select_tools(self, message):
        return []


class FakeExternalActionSelectionService:
    def select_action(self, message, allowed_action_ids=None):
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": "blocked.action",
            },
        }


class FakeExecuteToolUseCase:
    def execute(self, request):
        raise AssertionError("blocked action should not execute")


def test_external_action_is_blocked_when_not_allowed():
    service = ChatToolContextService(
        tool_selection_service=FakeToolSelectionService(),
        execute_tool_use_case=FakeExecuteToolUseCase(),
        external_action_selection_service=FakeExternalActionSelectionService(),
    )

    result = service.build_context(
        user_id="user",
        access_token="token",
        message="consulta",
        allowed_action_ids=["allowed.action"],
    )

    assert result == {
        "context": "",
        "toolCalls": [],
    }
