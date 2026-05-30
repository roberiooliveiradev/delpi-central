from app.application.services.chat_follow_up_suggestion_service import (
    ChatFollowUpSuggestionService,
)


def test_classify_product_outcome_from_tool_path():
    outcome = ChatFollowUpSuggestionService.classify_outcome(
        answer="Cadastro do produto 10080001",
        tool_calls=[{"path": "/products/10080001/analyser"}],
    )

    assert outcome == "product"


def test_classify_empty_outcome():
    outcome = ChatFollowUpSuggestionService.classify_outcome(
        answer="Não encontrei registros para esse filtro.",
        tool_calls=[],
    )

    assert outcome == "empty"


def test_build_follow_up_suggestions_with_product_code_from_message():
    suggestions = ChatFollowUpSuggestionService.build(
        message="me fale do produto 10080099",
        answer="Produto 10080099 cadastrado.",
        tool_calls=[{"metadata": {"path": "/products/10080099/analyser", "ok": True}}],
    )

    assert suggestions
    assert all("10080099" in item["query"] for item in suggestions)
    assert all("{product_code}" not in item["query"] for item in suggestions)
    assert suggestions[0]["label"] == "Ver estoque"
    assert suggestions[0]["query"] == "qual o estoque do produto 10080099?"


def test_build_follow_up_uses_working_memory_product_code():
    suggestions = ChatFollowUpSuggestionService.build(
        message="e o estoque?",
        answer="Saldo disponível.",
        tool_calls=[],
        workspace_context={
            "workingMemory": {"lastEntities": {"productCode": "10080001"}},
        },
    )

    assert suggestions
    product_queries = [
        item["query"]
        for item in suggestions
        if "{product_code}" not in item["query"] and item["label"] != "O que você pode fazer?"
    ]

    assert product_queries
    assert all("10080001" in query for query in product_queries)


def test_build_skips_product_chips_without_code():
    suggestions = ChatFollowUpSuggestionService.build(
        message="o que você pode fazer?",
        answer="Posso ajudar com consultas autorizadas.",
        tool_calls=[],
    )

    labels = {item["label"] for item in suggestions}

    assert "Ver estoque" not in labels
    assert "O que você pode fazer?" in labels


def test_follow_up_queries_use_operational_phrases():
    suggestions = ChatFollowUpSuggestionService.build(
        message="me fale do produto 10080001",
        answer="Resumo do produto.",
        tool_calls=[{"metadata": {"path": "/products/10080001/summary", "ok": True}}],
    )

    by_label = {item["label"]: item["query"] for item in suggestions}

    assert by_label["Ver fornecedores"] == "liste os fornecedores do produto 10080001"
    assert by_label["Ver estrutura"] == "mostre a estrutura do produto 10080001"
    assert by_label["Onde é usado?"] == "onde o produto 10080001 é usado?"


def test_attach_skips_when_agent_disables_follow_ups():
    metadata: dict = {}

    ChatFollowUpSuggestionService.attach_to_assistant_metadata(
        metadata,
        message="estoque",
        answer="Saldo disponível.",
        tool_calls=[{"path": "/stock"}],
        workspace_context={
            "agent": {
                "name": "Agente",
                "metadata": {
                    "personality": {"suggestFollowUps": False},
                },
            },
        },
    )

    assert "followUpSuggestions" not in metadata
