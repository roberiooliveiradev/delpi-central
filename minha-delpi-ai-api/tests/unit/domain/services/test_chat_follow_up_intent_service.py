from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService


def test_follow_up_without_explicit_code():
    assert ChatFollowUpIntentService.is_operational_follow_up("agora fornecedores") is True


def test_not_follow_up_with_product_code():
    assert (
        ChatFollowUpIntentService.is_operational_follow_up("estoque do produto 10080001")
        is False
    )


def test_follow_up_type_stock():
    assert ChatFollowUpIntentService.follow_up_type("agora estoque") == "stock"
