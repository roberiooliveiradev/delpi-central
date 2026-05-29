"""Testes do catálogo agentic por intent (Onda 11.3.1)."""

from app.application.services.chat_agentic_tool_loop_service import (
    ChatAgenticToolLoopService,
)
from app.domain.services.chat_agentic_catalog_service import ChatAgenticCatalogService
from app.infrastructure.config.settings import Settings


def _action(action_id: str, path: str, operation_id: str = "") -> dict:
    return {
        "actionId": action_id,
        "path": path,
        "operationId": operation_id or action_id,
        "summary": path,
        "method": "GET",
        "parametersSchema": [
            {"name": "code", "in": "path", "required": True},
        ],
    }


class FakeRepository:
    def __init__(self, actions: list[dict]):
        self.actions = actions
        self.calls: list[dict] = []

    def find_candidate_actions(self, message, limit=12, allowed_action_ids=None):
        self.calls.append(
            {
                "message": message,
                "limit": limit,
                "allowed_action_ids": allowed_action_ids,
            }
        )
        return self.actions[:limit]


def test_build_action_ids_respects_max_catalog_limit():
    repo = FakeRepository(
        [_action(f"action-{index}", f"/products/{index}/stock") for index in range(20)]
    )
    allowed = [f"action-{index}" for index in range(20)]

    action_ids = ChatAgenticCatalogService.build_action_ids(
        "estoque do produto 10080022",
        allowed,
        repo,
    )

    assert len(action_ids) == Settings.CHAT_AGENTIC_CATALOG_MAX_ACTIONS
    assert repo.calls[0]["limit"] >= Settings.CHAT_AGENTIC_CATALOG_MAX_ACTIONS


def test_stock_intent_prioritizes_stock_action_over_analyser():
    repo = FakeRepository(
        [
            _action("analyser-action", "/products/{code}/analyser", "get_product_analyser"),
            _action("stock-action", "/products/{code}/stock", "get_product_stock"),
            _action("rol-action", "/commercial/rol/series", "get_commercial_rol_series"),
        ]
    )

    action_ids = ChatAgenticCatalogService.build_action_ids(
        "estoque do produto 10080022",
        ["analyser-action", "stock-action", "rol-action"],
        repo,
    )

    assert action_ids[0] == "stock-action"


def test_structure_intent_prioritizes_structure_action():
    repo = FakeRepository(
        [
            _action("stock-action", "/products/{code}/stock", "get_product_stock"),
            _action("structure-action", "/products/{code}/structure", "get_product_structure"),
        ]
    )

    action_ids = ChatAgenticCatalogService.build_action_ids(
        "estrutura do produto 90260143",
        ["stock-action", "structure-action"],
        repo,
    )

    assert action_ids[0] == "structure-action"


def test_build_slim_catalog_returns_ranked_schemas():
    repo = FakeRepository(
        [
            _action("stock-action", "/products/{code}/stock", "get_product_stock"),
            _action("structure-action", "/products/{code}/structure", "get_product_structure"),
        ]
    )

    catalog = ChatAgenticCatalogService.build_slim_catalog(
        "estoque do produto 10080022",
        ["stock-action", "structure-action"],
        repo,
    )

    assert catalog[0]["actionId"] == "stock-action"
    assert catalog[0]["parameters"][0]["name"] == "code"
    assert catalog[0]["exampleArguments"]["parameters"]["code"] == "10080022"


def test_agentic_loop_exposes_catalog_metadata(monkeypatch):
    repo = FakeRepository([_action("stock-action", "/products/{code}/stock")])

    class FakeLlm:
        def generate(self, messages):
            return '{"tools":[],"arguments":{},"done":true}'

    service = ChatAgenticToolLoopService(
        llm_gateway=FakeLlm(),
        execute_tool_use_case=object(),
        external_action_repository=repo,
    )
    monkeypatch.setattr(
        service,
        "_resolve_settings",
        lambda: {"enabled": True, "max_steps": 1},
    )

    result = service.extend_tool_context(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        message="estoque do produto 10080022",
        tool_context={"context": "", "toolCalls": []},
        allowed_tool_names=None,
        allowed_action_ids=["stock-action", "rol-action"],
    )

    assert result.get("agentic", {}).get("catalogSize") == 1
    assert result.get("agentic", {}).get("catalogMaxActions") == Settings.CHAT_AGENTIC_CATALOG_MAX_ACTIONS


def test_planner_cannot_run_action_outside_catalog(monkeypatch):
    repo = FakeRepository([_action("stock-action", "/products/{code}/stock")])

    executed: list[str] = []

    class FakeLlm:
        def generate(self, messages):
            return '{"tools":["action:rol-action"],"arguments":{},"done":true}'

    class FakeExecuteTool:
        def execute(self, request):
            from app.application.dto.execute_tool_response import ExecuteToolResponse

            executed.append(str(request.arguments.get("actionId") or request.tool_name))
            return ExecuteToolResponse(name=request.tool_name, data={}, metadata={"ok": True})

    service = ChatAgenticToolLoopService(
        llm_gateway=FakeLlm(),
        execute_tool_use_case=FakeExecuteTool(),
        external_action_repository=repo,
    )
    monkeypatch.setattr(
        service,
        "_resolve_settings",
        lambda: {"enabled": True, "max_steps": 1},
    )

    result = service.extend_tool_context(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        message="estoque do produto 10080022",
        tool_context={"context": "", "toolCalls": []},
        allowed_tool_names=None,
        allowed_action_ids=["stock-action", "rol-action"],
    )

    assert executed == []
    assert result["toolCalls"] == []
