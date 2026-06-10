from unittest.mock import MagicMock

from app.application.services.chat_external_action_orchestration_service import (
    ChatExternalActionOrchestrationService,
)
from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService


def test_action_planning_factory_explicit_code_ignores_context_items():
    codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
        "status fabril do produto 90262401 hoje",
        memory_snapshot={
            "userContextItems": [
                {
                    "id": "1",
                    "content": "90269002",
                    "extractedEntities": {"productCode": "90269002"},
                },
            ],
        },
    )

    assert codes == ["90262401"]


def test_action_planning_codes_only_from_message_when_present():
    codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
        "estoque do produto 10080099",
        conversation_context=(
            "assistant: Produto 10080001: A\nassistant: Produto 10080002: B"
        ),
    )

    assert codes == ["10080099"]


def test_action_planning_followup_resolves_single_code_from_context():
    codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
        "estoque desse produto",
        conversation_context="assistant: Produto 10080047: TERM. PINO",
    )

    assert codes == ["10080047"]


def test_action_planning_estoque_without_code_uses_memory_context_items():
    codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
        "estoque",
        memory_snapshot={
            "userContextItems": [
                {
                    "id": "1",
                    "content": "90260140",
                    "extractedEntities": {"productCode": "90260140"},
                },
                {
                    "id": "2",
                    "content": "produto 10080014",
                    "extractedEntities": {"productCode": "10080014"},
                },
            ],
        },
    )

    assert codes == ["90260140", "10080014"]


def test_action_planning_ignores_date_tokens_in_ov_list_question():
    codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
        "listar ov de 01/04/2026 a 30/04/2026"
    )

    assert codes == []


def test_plan_actions_prefers_sale_orders_list_over_product_sales():
    selection_service = ExternalActionSelectionService(MagicMock())
    selection_service._list_allowed_candidates = MagicMock(
        return_value=[
            {
                "actionId": "api_delpi.sales.list_sale_orders",
                "method": "GET",
                "path": "/sales",
                "operationId": "list_sale_orders",
                "parametersSchema": [
                    {"name": "date_start"},
                    {"name": "date_end"},
                    {"name": "page"},
                    {"name": "page_size"},
                ],
            }
        ]
    )

    planned = ChatExternalActionOrchestrationService.plan_actions(
        selection_service,
        message="listar ov de 01/04/2026 a 30/04/2026",
        allowed_action_ids=["api_delpi.sales.list_sale_orders"],
    )

    assert len(planned) == 1
    assert planned[0]["arguments"]["actionId"] == "api_delpi.sales.list_sale_orders"
    assert planned[0]["arguments"]["parameters"]["date_start"] == "01-04-2026"
    assert planned[0]["arguments"]["parameters"]["date_end"] == "30-04-2026"
