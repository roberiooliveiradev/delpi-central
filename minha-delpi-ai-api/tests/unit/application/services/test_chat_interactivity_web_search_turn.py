"""Próximos passos coerentes após pesquisa web (chat comum e agente)."""

from app.application.services.chat_follow_up_suggestion_service import (
    ChatFollowUpSuggestionService,
)
from app.application.services.chat_interactivity_suggestion_service import (
    ChatInteractivitySuggestionService,
)
from app.application.services.chat_web_search_follow_up_service import (
    ChatWebSearchFollowUpService,
)


def _web_search_tool_calls():
    return [
        {
            "name": "web_search",
            "metadata": {"searchStatus": "success", "count": 3},
        }
    ]


def test_follow_up_skips_generic_operational_chips_on_web_turn():
    metadata: dict = {}

    ChatFollowUpSuggestionService.attach_to_assistant_metadata(
        metadata,
        message="qual a capital da frança?",
        answer="A capital da França é Paris.",
        tool_calls=_web_search_tool_calls(),
        workspace_context={"capabilities": {}, "userActivatedAgent": False},
    )

    assert "followUpSuggestions" not in metadata
    assert ChatFollowUpSuggestionService.classify_outcome(
        answer="A capital da França é Paris.",
        tool_calls=_web_search_tool_calls(),
    ) == "web"


def test_interactivity_prioritizes_web_chips_on_web_turn():
    metadata: dict = {
        "followUpSuggestions": [
            {"label": "Consultar produto", "query": "me fale do produto {{productCode}}"},
            {"label": "O que você pode fazer?", "query": "o que você pode fazer?"},
        ],
    }

    ChatWebSearchFollowUpService.attach_to_assistant_metadata(
        metadata,
        tool_context={
            "webSearchPayload": {
                "searchStatus": "success",
                "query": "qual a capital da franca dados atuais internet",
            }
        },
        message="qual a capital da frança?",
    )

    ChatInteractivitySuggestionService.attach_to_assistant_metadata(
        metadata,
        workspace_context={"capabilities": {"canvas": True}},
        tool_calls=_web_search_tool_calls(),
        intent_route={"intent": "operational_query", "requiresWeb": True},
    )

    interactivity = metadata["interactivity"]
    primary_labels = [item["label"] for item in interactivity["suggestions"]]

    assert "Consultar produto" not in primary_labels
    assert "Abrir fontes" in primary_labels
    assert "Buscar em inglês" in primary_labels
