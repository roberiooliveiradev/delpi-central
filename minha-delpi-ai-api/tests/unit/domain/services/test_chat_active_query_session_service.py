from datetime import date
from unittest.mock import patch

from app.application.services.chat_active_pending_service import (
    ChatActivePendingService,
)
from app.application.services.chat_external_action_orchestration_service import (
    ChatExternalActionOrchestrationService,
)
from app.domain.services.chat_active_query_session_service import (
    ChatActiveQuerySessionService,
)
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)


def test_compose_selection_message_after_missing_product_code_reply():
    history = [
        {
            "role": "assistant",
            "content": "Informe o código.",
            "metadata": {
                "activePending": {
                    "kind": "missing_product_code",
                    "expectedParam": "productCode",
                    "context": {
                        "originalMessage": "estoque",
                        "subIntent": "stock",
                        "expectedParam": "productCode",
                    },
                }
            },
        }
    ]

    composed = ChatActiveQuerySessionService.compose_selection_message(
        "90263059",
        previous_messages=history,
    )

    assert composed == "estoque 90263059"


def test_compose_selection_message_for_multiple_codes_after_pending():
    pending = {
        "kind": "missing_product_code",
        "context": {"originalMessage": "estoque"},
    }

    resolved = ChatActivePendingService.try_resolve(
        "90263059, 10080099",
        pending,
    )

    assert resolved is not None
    assert resolved["resumeMessage"] == "estoque 90263059, 10080099"
    assert resolved["resolvedParams"]["productCode"] == "90263059"
    assert resolved["resolvedParams"]["productCodes"] == "90263059,10080099"


def test_compose_selection_message_continues_active_stock_session():
    history = [
        {
            "role": "assistant",
            "content": "Estoque...",
            "metadata": {
                "activeQuery": {
                    "queryKind": "product_operational",
                    "subIntent": "stock",
                    "routeSegment": "stock",
                    "originalMessage": "estoque",
                    "expectedParam": "productCode",
                },
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/90263059/stock"},
                    }
                ],
            },
        }
    ]

    composed = ChatActiveQuerySessionService.compose_selection_message(
        "10080099",
        previous_messages=history,
    )

    assert composed == "estoque 10080099"


def test_active_session_does_not_continue_on_topic_change():
    session = {
        "subIntent": "stock",
        "routeSegment": "stock",
        "originalMessage": "estoque",
        "expectedParam": "productCode",
    }

    assert ChatActiveQuerySessionService.looks_like_topic_change(
        "estrutura do 90263059",
        session,
    )


def test_plan_actions_uses_composed_message_after_stock_session():
    class RecordingSelectionService:
        def __init__(self):
            self.messages: list[str] = []

        def select_action_for_product(self, *args, **kwargs):
            return None

        def select_action(
            self,
            message,
            allowed_action_ids=None,
            conversation_context=None,
            previous_messages=None,
            **kwargs,
        ):
            self.messages.append(message)
            return {
                "name": "execute_external_action",
                "arguments": {"actionId": "product-stock", "parameters": {}},
            }

    service = RecordingSelectionService()
    history = [
        {
            "role": "assistant",
            "metadata": {
                "activeQuery": {
                    "queryKind": "product_operational",
                    "subIntent": "stock",
                    "routeSegment": "stock",
                    "originalMessage": "estoque",
                    "expectedParam": "productCode",
                },
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/90263059/stock"},
                    }
                ],
            },
        }
    ]

    ChatExternalActionOrchestrationService.plan_actions(
        service,
        message="10080099",
        allowed_action_ids=["product-stock"],
        previous_messages=history,
        max_calls=3,
    )

    assert service.messages == ["estoque 10080099"]


def test_missing_product_code_prompt_for_bare_estoque():
    answer = ChatOperationalParameterService.resolve_missing_product_code_answer(
        "estoque"
    )

    assert answer is not None
    assert "código" in answer.lower() or "codigo" in answer.lower()


def test_build_session_from_successful_stock_turn():
    session = ChatActiveQuerySessionService.build_session_from_turn(
        message="estoque do produto 90263059",
        tool_context={
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {"ok": True, "path": "/products/90263059/stock"},
                }
            ]
        },
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {
                    "activePending": {
                        "kind": "missing_product_code",
                        "context": {"originalMessage": "estoque"},
                    }
                },
            }
        ],
    )

    assert session is not None
    assert session["subIntent"] == ChatProductQueryIntent.STOCK
    assert session["originalMessage"] == "estoque"
    assert session["expectedParam"] == "productCode"


def test_compose_selection_message_after_missing_date_reply():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "activePending": {
                    "kind": "missing_date",
                    "context": {
                        "originalMessage": "status fabril do 90263059",
                        "productCode": "90263059",
                    },
                }
            },
        }
    ]

    with patch("app.domain.services.chat_date_range_intent_service.date") as mock_date:
        mock_date.today.return_value = date(2026, 6, 9)

        composed = ChatActiveQuerySessionService.compose_selection_message(
            "hoje",
            previous_messages=history,
        )

    assert "90263059" in composed
    assert "hoje" in composed
