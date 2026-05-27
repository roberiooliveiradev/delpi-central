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

    def select_action(self, message, allowed_action_ids=None, conversation_context=None):
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
