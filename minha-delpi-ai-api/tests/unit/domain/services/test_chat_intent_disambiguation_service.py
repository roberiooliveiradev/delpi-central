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


def test_try_build_not_ambiguous_for_quem_fornece():
    result = ChatIntentDisambiguationService.try_build(
        "quem fornece o produto 10080022?",
        allowed_action_ids=["action-1"],
    )

    assert result is None


def test_try_build_not_ambiguous_for_full_analyser_phrases():
    queries = [
        "informações completas do produto 90260149",
        "análise integrada do cadastro, roteiro e estrutura do 90260149",
        "estrutura e roteiro do produto 90260149",
        "roteiro e inspeção do produto 90260149",
    ]

    for query in queries:
        assert ChatIntentDisambiguationService.try_build(
            query,
            allowed_action_ids=["action-1"],
        ) is None, query


def test_try_build_not_ambiguous_for_home_starter_queries():
    queries = [
        "me fale do produto 10080022",
        "qual o estoque do produto 10080022?",
        "mostre vendas do produto 10080022",
        "onde o produto 10080022 é usado?",
    ]

    for query in queries:
        assert ChatIntentDisambiguationService.try_build(
            query,
            allowed_action_ids=["action-1"],
        ) is None, query
