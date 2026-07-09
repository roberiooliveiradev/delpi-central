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


def _operational_context() -> dict:
    return {"userActivatedAgent": True, "actionsEnabled": True}


def test_build_follow_up_suggestions_use_placeholders_not_hardcoded_code():
    suggestions = ChatFollowUpSuggestionService.build(
        message="me fale do produto 10080099",
        answer="Produto 10080099 cadastrado.",
        tool_calls=[{"metadata": {"path": "/products/10080099/analyser", "ok": True}}],
        workspace_context=_operational_context(),
    )

    assert suggestions
    assert suggestions[0]["label"] == "Ver estoque"
    assert suggestions[0]["query"] == "qual o estoque do produto {{productCode}}?"
    assert "10080099" not in suggestions[0]["query"]
    assert "{product_code}" not in suggestions[0]["query"]


def test_build_includes_product_chips_even_without_resolved_code():
    suggestions = ChatFollowUpSuggestionService.build(
        message="o que você pode fazer?",
        answer="Posso ajudar com consultas autorizadas.",
        tool_calls=[],
    )

    labels = {item["label"] for item in suggestions}
    by_label = {item["label"]: item["query"] for item in suggestions}

    assert "Ver estoque" in labels
    assert by_label["Ver estoque"] == "qual o estoque do produto {{productCode}}?"
    assert "O que você pode fazer?" in labels


def test_follow_up_queries_use_operational_phrases_with_placeholders():
    suggestions = ChatFollowUpSuggestionService.build(
        message="me fale do produto 10080001",
        answer="Resumo do produto.",
        tool_calls=[{"metadata": {"path": "/products/10080001/summary", "ok": True}}],
        workspace_context=_operational_context(),
    )

    by_label = {item["label"]: item["query"] for item in suggestions}

    assert by_label["Ver fornecedores"] == "liste os fornecedores do produto {{productCode}}"
    assert by_label["Ver estrutura"] == "mostre a estrutura do produto {{productCode}}"
    assert by_label["Análise completa"] == "análise completa do produto {{productCode}}"


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
