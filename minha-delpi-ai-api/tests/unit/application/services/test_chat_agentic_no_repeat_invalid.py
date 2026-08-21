from app.application.services.chat_agentic_tool_loop_service import (
    ChatAgenticToolLoopService,
)
from app.domain.entities.tool_result import ToolResult
from app.domain.exceptions.external_action_exceptions import ExternalActionValidationError


class _FakeLlm:
    def __init__(self, plans: list[str]):
        self.plans = list(plans)
        self.calls = 0

    def generate(self, messages):
        self.calls += 1
        if not self.plans:
            return '{"tools":[],"done":true}'
        return self.plans.pop(0)


class _FakeExecute:
    def __init__(self):
        self.calls: list[dict] = []

    def execute(self, request):
        self.calls.append(
            {
                "tool_name": request.tool_name,
                "arguments": dict(request.arguments or {}),
            }
        )
        raise ExternalActionValidationError(
            "Missing required parameter: code",
            error_kind="missing_required_parameter",
            missing_parameter="code",
        )


class _FakeRepo:
    def find_candidate_actions(self, message, limit=12, allowed_action_ids=None):
        return [
            {
                "actionId": "api_delpi.products.get_product_drawing",
                "path": "/products/{code}/drawing",
                "method": "GET",
                "summary": "Desenho",
                "parametersSchema": [
                    {"name": "code", "in": "path", "required": True},
                ],
            }
        ]


class _FakeSettings:
    def resolve(self):
        class Runtime:
            agentic_loop_enabled = True
            agentic_loop_max_steps = 2

        return Runtime()


def test_agentic_loop_does_not_repeat_missing_required_parameter_action():
    llm = _FakeLlm(
        [
            '{"tools":["action:api_delpi.products.get_product_drawing"],'
            '"arguments":{"action:api_delpi.products.get_product_drawing":{"parameters":{}}},'
            '"done":false}',
            '{"tools":["action:api_delpi.products.get_product_drawing"],'
            '"arguments":{"action:api_delpi.products.get_product_drawing":{"parameters":{}}},'
            '"done":true}',
        ]
    )
    execute = _FakeExecute()
    service = ChatAgenticToolLoopService(
        llm_gateway=llm,
        execute_tool_use_case=execute,
        intelligence_settings_service=_FakeSettings(),
        external_action_repository=_FakeRepo(),
    )

    # Sem foco: action some do catálogo no rebuild; com foco vazio no 1º passo
    # a action ainda entra se o planner pedir — após missing_required, invalid_action_ids
    # impede a 2ª execução mesmo se o planner repetir.
    result = service.extend_tool_context(
        user_id="u1",
        access_token="t",
        message="buscar desenho 90261899",
        tool_context={"toolCalls": []},
        allowed_tool_names=[],
        allowed_action_ids=["api_delpi.products.get_product_drawing"],
    )

    assert len(execute.calls) == 1
    assert result["toolCalls"]
    assert result["toolCalls"][0]["metadata"]["errorKind"] == "missing_required_parameter"
