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


def test_follow_up_expedition_short_message():
    assert ChatFollowUpIntentService.is_operational_follow_up("e a expedição?") is True
    assert ChatFollowUpIntentService.follow_up_type("e a expedição?") == "shipping"


def test_follow_up_structure_exclusivity():
    message = "quais matérias-primas exclusivas existem na estrutura desse produto?"
    assert ChatFollowUpIntentService.is_operational_follow_up(message) is True
    assert ChatFollowUpIntentService.follow_up_type(message) == "structure_exclusivity"


def test_follow_up_structure_exclusivity_short_after_product_context():
    message = "quais são exclusivas?"
    assert ChatFollowUpIntentService.is_operational_follow_up(message) is True
    assert ChatFollowUpIntentService.follow_up_type(message) == "structure_exclusivity"


def test_follow_up_global_exclusive_catalog_is_not_structure_exclusivity_type():
    message = "Quais matérias-primas são exclusivas?"
    assert ChatFollowUpIntentService.is_operational_follow_up(message) is True
    assert ChatFollowUpIntentService.follow_up_type(message) is None
