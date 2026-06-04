from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_user_context_item_service import ChatUserContextItemService


def test_resolve_all_product_codes_from_context_items():
    items = [
        {
            "id": "a",
            "kind": "context",
            "label": "90260140",
            "content": "90260140",
            "extractedEntities": {"productCode": "90260140"},
        },
        {
            "id": "b",
            "kind": "context",
            "label": "produto 10080014",
            "content": "produto 10080014",
            "extractedEntities": {"productCode": "10080014"},
        },
    ]

    assert ChatUserContextItemService.resolve_all_product_codes_from_items(items) == [
        "90260140",
        "10080014",
    ]


def test_action_planning_uses_all_context_products_for_stock():
    memory = {
        "userContextItems": [
            {
                "id": "a",
                "kind": "context",
                "label": "90260140",
                "content": "90260140",
                "extractedEntities": {"productCode": "90260140"},
                "source": "user",
            },
            {
                "id": "b",
                "kind": "context",
                "label": "produto 10080014",
                "content": "produto 10080014",
                "extractedEntities": {"productCode": "10080014"},
                "source": "user",
            },
        ],
    }

    codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
        "estoque",
        conversation_context=None,
        memory_snapshot=memory,
    )

    assert codes == ["90260140", "10080014"]


def test_action_planning_single_code_in_message_ignores_extra_context():
    memory = {
        "userContextItems": [
            {
                "id": "a",
                "kind": "context",
                "content": "90260140",
                "extractedEntities": {"productCode": "90260140"},
            },
            {
                "id": "b",
                "kind": "context",
                "content": "10080014",
                "extractedEntities": {"productCode": "10080014"},
            },
        ],
    }

    codes = ChatAnalysisIntentService.extract_product_codes_for_action_planning(
        "estoque do produto 10080099",
        conversation_context=None,
        memory_snapshot=memory,
    )

    assert codes == ["10080099"]
