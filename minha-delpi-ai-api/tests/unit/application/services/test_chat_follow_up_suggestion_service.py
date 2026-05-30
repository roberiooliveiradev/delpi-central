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


def test_build_follow_up_suggestions_with_product_code():
    suggestions = ChatFollowUpSuggestionService.build(
        message="me fale do produto 10080099",
        answer="Produto 10080099 cadastrado.",
        tool_calls=[{"path": "/products/10080099"}],
    )

    assert suggestions
    assert suggestions[0]["label"]
    assert "10080099" in suggestions[0]["query"]


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
