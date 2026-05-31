from app.domain.services.chat_intent_disambiguation_service import ChatIntentDisambiguationService


def test_try_build_ambiguous_product_code():
    result = ChatIntentDisambiguationService.try_build(
        "produto 10080001",
        allowed_action_ids=["action-1"],
    )

    assert result is not None
    assert "10080001" in result["directAnswer"]
    assert len(result["suggestions"]) >= 4
    assert result["suggestions"][0]["label"] == "Cadastro"


def test_try_build_not_ambiguous_for_stock():
    result = ChatIntentDisambiguationService.try_build(
        "qual o estoque do produto 10080001?",
        allowed_action_ids=["action-1"],
    )

    assert result is None
