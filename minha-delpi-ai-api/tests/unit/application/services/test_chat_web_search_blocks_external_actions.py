from unittest.mock import patch

from app.application.services.chat_tool_context_service import ChatToolContextService
from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.domain.entities.tool_result import ToolResult
from app.domain.services.tool_selection_service import ToolSelectionService


class FakeExternalActionSelectionService:
    def select_action(self, message, allowed_action_ids=None, **kwargs):
        return {
            "name": "execute_external_action",
            "arguments": {"actionId": "api_externa.products.search"},
            "reason": "Busca de produto",
        }


class FakeExecuteToolUseCase:
    tools = {"web_search": object(), "execute_external_action": object()}

    def execute(self, request):
        if request.tool_name == "web_search":
            return ToolResult(
                name="web_search",
                data={
                    "query": "python programming language",
                    "searchStatus": "success",
                    "results": [
                        {
                            "title": "Python",
                            "snippet": "High-level language.",
                            "url": "https://example.com/python",
                            "source": "instant_answer",
                        }
                    ],
                },
                metadata={"source": "web_search", "searchStatus": "success"},
            )

        raise AssertionError(
            f"execute_external_action não deveria rodar com web_search exclusivo: {request.tool_name}"
        )


@patch(
    "app.domain.services.chat_web_search_intent_service.ChatWebSearchIntentService.is_feature_enabled",
    return_value=True,
)
def test_web_search_blocks_external_action_in_tool_context(_enabled):
    service = ChatToolContextService(
        tool_selection_service=ToolSelectionService(),
        execute_tool_use_case=FakeExecuteToolUseCase(),
        external_action_selection_service=FakeExternalActionSelectionService(),
    )

    result = service.build_context(
        user_id="user-1",
        access_token="token",
        message="pesquise na internet sobre Python linguagem de programação",
        allowed_action_ids=["api_externa.products.search"],
        actions_enabled=True,
    )

    tool_names = [call["name"] for call in result["toolCalls"]]

    assert tool_names == ["web_search"]
    assert result.get("directAnswer") in (None, "")
    assert "web_search" in result["context"]
    assert "execute_external_action" not in result["context"]


@patch(
    "app.domain.services.chat_web_search_intent_service.ChatWebSearchIntentService.is_feature_enabled",
    return_value=True,
)
def test_external_action_selection_returns_none_for_web_search(_enabled):
    service = ExternalActionSelectionService(repository=object())

    selected = service.select_action(
        "pesquise na internet sobre Python linguagem de programação",
        allowed_action_ids=["api_externa.products.search"],
    )

    assert selected is None
