from app.application.services.chat_tool_context_service import ChatToolContextService


class FakeToolSelectionService:
    def select_tools(self, message):
        return []


class FakeExternalActionSelectionService:
    def select_action(self, message, allowed_action_ids=None, **kwargs):
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": "api.product.get",
            },
        }


class FakeExecuteToolUseCase:
    def execute(self, request):
        raise AssertionError("external action should not execute")


def test_chat_common_does_not_execute_external_action_without_agent_actions():
    service = ChatToolContextService(
        tool_selection_service=FakeToolSelectionService(),
        execute_tool_use_case=FakeExecuteToolUseCase(),
        external_action_selection_service=FakeExternalActionSelectionService(),
    )

    result = service.build_context(
        user_id="user",
        access_token="token",
        message="produto 10010011",
        allowed_action_ids=[],
        actions_enabled=False,
    )

    assert result["context"] == ""
    assert result["toolCalls"] == []
    assert "nativeToolCalling" in result


def test_agent_action_executes_only_when_allowed():
    called = {"value": False}

    class ExecuteToolUseCase:
        def execute(self, request):
            called["value"] = True

            class Result:
                name = "execute_external_action"
                data = {"ok": True}
                metadata = {
                    "provider": "api",
                    "actionId": "api.product.get",
                    "path": "/products/{code}",
                    "statusCode": 200,
                    "ok": True,
                }

            return Result()

    service = ChatToolContextService(
        tool_selection_service=FakeToolSelectionService(),
        execute_tool_use_case=ExecuteToolUseCase(),
        external_action_selection_service=FakeExternalActionSelectionService(),
    )

    result = service.build_context(
        user_id="user",
        access_token="token",
        message="produto 10010011",
        allowed_action_ids=["api.product.get"],
        actions_enabled=True,
    )

    assert called["value"] is True
    assert result["toolCalls"][0]["name"] == "execute_external_action"
    assert '"ok": true' in result["toolCalls"][0]["metadata"]["responsePreview"]
