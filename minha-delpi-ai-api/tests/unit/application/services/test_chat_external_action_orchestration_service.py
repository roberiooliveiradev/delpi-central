from app.application.services.chat_external_action_orchestration_service import (
    ChatExternalActionOrchestrationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)


class FakeSelectionService:
    def __init__(self):
        self.product_calls: list[tuple[str, str]] = []

    def select_action_for_product(
        self,
        message,
        *,
        product_code,
        allowed_action_ids=None,
        intent=None,
        route_segment=None,
    ):
        self.product_calls.append((product_code, intent))
        return {
            "name": "execute_external_action",
            "arguments": {
                "actionId": "product-structure",
                "parameters": {"code": product_code},
            },
            "reason": f"estrutura {product_code}",
        }

    def select_action(
        self,
        message,
        allowed_action_ids=None,
        conversation_context=None,
        previous_messages=None,
    ):
        return {
            "name": "execute_external_action",
            "arguments": {"actionId": "product-stock"},
            "reason": "única",
        }


def test_plan_actions_for_multiple_product_codes():
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="estrutura do produto 90260077 e do 90260088",
        allowed_action_ids=["product-structure"],
        max_calls=5,
    )

    assert len(planned) == 2
    assert service.product_calls[0][0] == "90260077"
    assert service.product_calls[1][0] == "90260088"
    assert service.product_calls[0][1] == ChatProductQueryIntent.STRUCTURE


def test_plan_actions_comparison_fetches_missing_structure(monkeypatch):
    monkeypatch.setattr(
        "app.application.services.chat_external_action_orchestration_service.Settings.CHAT_MULTI_ACTION_ENABLED",
        True,
    )
    service = FakeSelectionService()
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260077/structure",
                            "responsePreview": '{"root":{"code":"90260077","description":"A","type":"PA","unit":"MI","quantity":1},"items":[]}',
                        },
                    }
                ]
            },
        }
    ]

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="compare as estruturas",
        allowed_action_ids=["product-structure"],
        conversation_context="90260077 e 90260088",
        previous_messages=history,
        max_calls=3,
    )

    assert len(planned) == 1
    assert service.product_calls[0][0] == "90260088"


def test_plan_actions_single_code_uses_select_action():
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="estoque do produto 10080047",
        allowed_action_ids=["product-stock"],
    )

    assert len(planned) == 1
    assert planned[0]["arguments"]["actionId"] == "product-stock"
    assert not service.product_calls


def test_plan_actions_ignores_history_codes_when_message_names_product():
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="estoque do produto 10080099",
        allowed_action_ids=["product-stock"],
        conversation_context=(
            "assistant: Produto 10080001: CABO A\n"
            "assistant: Produto 10080002: CABO B\n"
            "assistant: Produto 10080003: CABO C\n"
        ),
        max_calls=5,
    )

    assert len(planned) == 1
    assert planned[0]["arguments"]["actionId"] == "product-stock"
    assert len(service.product_calls) == 0


def test_plan_actions_followup_uses_single_code_from_context():
    service = FakeSelectionService()

    planned = ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="busque o estoque desse produto",
        allowed_action_ids=["product-stock"],
        conversation_context="assistant: Produto 10080047: TERM. PINO RETO.",
        max_calls=5,
    )

    assert len(planned) == 1
    assert not service.product_calls


def test_plan_actions_pagination_follow_up_uses_select_action():
    from app.application.services.external_actions.external_action_selection_service import (
        ExternalActionSelectionService,
    )

    class Repo:
        actions = [
            {
                "actionId": "parents-action",
                "method": "GET",
                "path": "/products/{code}/parents",
                "operationId": "get_product_parents",
                "summary": "Produtos pai",
                "parametersSchema": [
                    {"name": "code", "in": "path", "required": True},
                    {"name": "page", "in": "query"},
                    {"name": "page_size", "in": "query"},
                ],
            }
        ]

        def find_candidate_actions(self, message, limit=80, allowed_action_ids=None):
            return self.actions

    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "parents-action",
                            "parameters": {
                                "code": "10080022",
                                "page": 1,
                                "page_size": 25,
                            },
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/parents",
                            "actionId": "parents-action",
                            "dataCoverageNotice": {"kind": "pagination"},
                        },
                    }
                ]
            },
        },
    ]

    selection_service = ExternalActionSelectionService(Repo())

    planned = ChatExternalActionOrchestrationService.plan_actions(
        selection_service,
        message="aumente para 50 linhas",
        allowed_action_ids=["parents-action"],
        previous_messages=history,
    )

    assert len(planned) == 1
    params = planned[0]["arguments"]["parameters"]
    assert params["code"] == "10080022"
    assert params["page_size"] == 50
