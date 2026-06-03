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


def test_agentic_skipped_for_normas_guidance(monkeypatch):
    service = ChatAgenticToolLoopService(
        llm_gateway=FakeLlm(),
        execute_tool_use_case=FakeExecuteTool(),
        external_action_repository=FakeRepository(
            [{"actionId": "api_delpi.products.search_products"}],
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
        message="como descrever um terminal?",
        tool_context={"context": "", "toolCalls": []},
        allowed_tool_names=None,
        allowed_action_ids=["api_delpi.products.search_products"],
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
    assert calls[0]["limit"] >= Settings.CHAT_AGENTIC_CATALOG_MAX_ACTIONS


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


def test_agentic_skipped_after_successful_stock_value_kpi(monkeypatch):
    service = ChatAgenticToolLoopService(
        llm_gateway=FakeLlm(),
        execute_tool_use_case=FakeExecuteTool(),
        external_action_repository=FakeRepository(
            [{"actionId": "api_delpi.suprimentos.get_supplies_stock_value"}]
        ),
    )
    monkeypatch.setattr(
        service,
        "_resolve_settings",
        lambda: {"enabled": True, "max_steps": 1},
    )

    tool_context = {
        "directAnswer": "Valor Total de Estoque",
        "skipRag": True,
        "context": "consulta ok",
        "toolCalls": [
            {
                "name": "execute_external_action",
                "arguments": {
                    "actionId": "api_delpi.suprimentos.get_supplies_stock_value",
                },
                "metadata": {
                    "ok": True,
                    "path": "/supplies/stock-value",
                    "presentation": {
                        "type": "kpi",
                        "title": "Valor Total de Estoque",
                    },
                },
            }
        ],
    }

    result = service.extend_tool_context(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        message="qual o valor total de estoque da empresa",
        tool_context=tool_context,
        allowed_tool_names=None,
        allowed_action_ids=["api_delpi.suprimentos.get_supplies_stock_value"],
    )

    assert result["toolCalls"] == tool_context["toolCalls"]
    assert result["directAnswer"] == "Valor Total de Estoque"
    assert result.get("skipRag") is True


def test_planner_receives_slim_openapi_schemas(monkeypatch):
    captured: list[list[dict]] = []

    class CapturingLlm:
        def generate(self, messages):
            captured.append(messages)
            return '{"tools":[],"arguments":{},"done":true}'

    service = ChatAgenticToolLoopService(
        llm_gateway=CapturingLlm(),
        execute_tool_use_case=FakeExecuteTool(),
        external_action_repository=FakeRepository(
            [
                {
                    "actionId": "stock-action",
                    "method": "GET",
                    "path": "/products/{code}/stock",
                    "summary": "Consulta estoque",
                    "parametersSchema": [
                        {"name": "code", "in": "path", "required": True},
                        {"name": "branch", "in": "query"},
                    ],
                }
            ]
        ),
    )
    monkeypatch.setattr(
        service,
        "_resolve_settings",
        lambda: {"enabled": True, "max_steps": 1},
    )

    service.extend_tool_context(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        message="estoque do produto 10080022",
        tool_context={"context": "", "toolCalls": []},
        allowed_tool_names=None,
        allowed_action_ids=["stock-action"],
    )

    assert captured
    user_content = captured[0][1]["content"]
    assert "Actions OpenAPI (descrição + parâmetros + exemplos):" in user_content
    assert '"actionId": "stock-action"' in user_content
    assert '"exampleArguments"' in user_content


def test_looks_like_failure_detection():
    assert ChatAgenticToolLoopService._looks_like_failure({"ok": False}) is True
    assert ChatAgenticToolLoopService._looks_like_failure({"statusCode": 404}) is True
    assert ChatAgenticToolLoopService._looks_like_failure({"statusCode": 500}) is True
    assert ChatAgenticToolLoopService._looks_like_failure({"ok": True}) is False
    assert ChatAgenticToolLoopService._looks_like_failure({"statusCode": 200}) is False
    assert ChatAgenticToolLoopService._looks_like_failure({}) is False


def test_summarize_failure_includes_label_status_and_reason():
    summary = ChatAgenticToolLoopService._summarize_failure(
        {"statusCode": 404, "error": "produto não encontrado"},
        "stock-action",
    )
    assert "stock-action" in summary
    assert "404" in summary
    assert "produto não encontrado" in summary


def test_failed_step_feeds_planner_with_alternative_instruction(monkeypatch):
    """Após uma falha, o próximo planejamento deve receber as falhas e a
    instrução para tentar uma abordagem alternativa (contorno)."""
    captured: list[list[dict]] = []

    class PlannerLlm:
        def __init__(self):
            self.calls = 0

        def generate(self, messages):
            captured.append(messages)
            self.calls += 1
            if self.calls == 1:
                return '{"tools":["action:stock-action"],"arguments":{},"done":false}'
            return '{"tools":[],"arguments":{},"done":true}'

    class FailingExecuteTool:
        def execute(self, request):
            raise RuntimeError("upstream timeout")

    service = ChatAgenticToolLoopService(
        llm_gateway=PlannerLlm(),
        execute_tool_use_case=FailingExecuteTool(),
        external_action_repository=FakeRepository([{"actionId": "stock-action"}]),
    )
    monkeypatch.setattr(
        service,
        "_resolve_settings",
        lambda: {"enabled": True, "max_steps": 2},
    )

    result = service.extend_tool_context(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="token",
        message="estoque do produto 10080022",
        tool_context={"context": "", "toolCalls": []},
        allowed_tool_names=None,
        allowed_action_ids=["stock-action"],
    )

    assert len(captured) >= 2
    second_user_content = captured[1][1]["content"]
    assert "já falharam" in second_user_content.lower()
    assert "upstream timeout" in second_user_content
    second_system_content = captured[1][0]["content"]
    assert "ALTERNATIVA" in second_system_content

    failed_calls = [
        call
        for call in (result.get("toolCalls") or [])
        if call.get("metadata", {}).get("ok") is False
    ]
    assert failed_calls, "falha deve ser propagada ao tool_context para §27 enriquecer"
