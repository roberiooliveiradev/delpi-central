from app.application.services.chat_agentic_tool_loop_service import (
    ChatAgenticToolLoopService,
)
from app.infrastructure.config.settings import Settings


class FakeLlm:
    def generate(self, messages):
        return '{"tools":["action:stock-action"],"arguments":{},"done":true}'


class FakeExecuteTool:
    def execute(self, request):
        from app.application.dto.execute_tool_response import ExecuteToolResponse

        return ExecuteToolResponse(
            name=request.tool_name,
            data={"success": True},
            metadata={"ok": True},
        )


class FakeRepository:
    def __init__(self, actions):
        self.actions = actions

    def find_candidate_actions(self, message, limit=12, allowed_action_ids=None):
        return self.actions[:limit]


def test_agentic_skipped_when_stock_without_product_code(monkeypatch):
    service = ChatAgenticToolLoopService(
        llm_gateway=FakeLlm(),
        execute_tool_use_case=FakeExecuteTool(),
        external_action_repository=FakeRepository(
            [
                {"actionId": "commercial-rol"},
                {"actionId": "stock-action"},
            ]
        ),
    )
    monkeypatch.setattr(
        service,
        "_resolve_settings",
        lambda: {"enabled": True, "max_steps": 1},
    )

    result = service.extend_tool_context(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        message="estoque do produto",
        tool_context={"context": "", "toolCalls": []},
        allowed_tool_names=None,
        allowed_action_ids=["commercial-rol", "stock-action"],
    )

    assert result["toolCalls"] == []


def test_agentic_catalog_uses_semantic_candidates_not_first_ids(monkeypatch):
    calls = []

    class TrackingRepo(FakeRepository):
        def find_candidate_actions(self, message, limit=12, allowed_action_ids=None):
            calls.append({"message": message, "limit": limit})
            return [{"actionId": "stock-action"}]

    service = ChatAgenticToolLoopService(
        llm_gateway=FakeLlm(),
        execute_tool_use_case=FakeExecuteTool(),
        external_action_repository=TrackingRepo([]),
    )
    monkeypatch.setattr(
        service,
        "_resolve_settings",
        lambda: {"enabled": True, "max_steps": 1},
    )

    service.extend_tool_context(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        message="estoque do produto 10080099",
        tool_context={"context": "", "toolCalls": []},
        allowed_tool_names=None,
        allowed_action_ids=["commercial-rol", "stock-action"],
    )

    assert calls
    assert calls[0]["limit"] == Settings.CHAT_AGENTIC_CATALOG_MAX_ACTIONS


def test_agentic_skipped_on_stock_branch_refinement(monkeypatch):
    service = ChatAgenticToolLoopService(
        llm_gateway=FakeLlm(),
        execute_tool_use_case=FakeExecuteTool(),
        external_action_repository=FakeRepository(
            [
                {"actionId": "commercial-rol"},
                {"actionId": "stock-action"},
            ]
        ),
    )
    monkeypatch.setattr(
        service,
        "_resolve_settings",
        lambda: {"enabled": True, "max_steps": 1},
    )

    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        {
            "role": "assistant",
            "content": "Estoque",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/stock",
                        },
                    }
                ]
            },
        },
    ]

    result = service.extend_tool_context(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        message="filtre filial 02",
        tool_context={"context": "", "toolCalls": []},
        allowed_tool_names=None,
        allowed_action_ids=["commercial-rol", "stock-action"],
        previous_messages=history,
    )

    assert result["toolCalls"] == []
