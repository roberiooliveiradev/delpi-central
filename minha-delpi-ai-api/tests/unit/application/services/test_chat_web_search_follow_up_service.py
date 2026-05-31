from app.application.services.chat_web_search_follow_up_service import (
    ChatWebSearchFollowUpService,
)


def test_build_success_suggestions_with_topic():
    suggestions = ChatWebSearchFollowUpService.build(
        payload={
            "searchStatus": "success",
            "query": "DELPI Conexões Elétricas",
            "preferOfficial": True,
        },
    )

    assert len(suggestions) >= 4
    labels = {item["label"] for item in suggestions}
    assert "Colocar na lousa" in labels
    assert any("{{searchQuery}}" in item["query"] for item in suggestions)


def test_build_no_results_includes_attachment_chip():
    suggestions = ChatWebSearchFollowUpService.build(
        payload={"searchStatus": "no_results", "query": "tyco valve"},
        had_attachments=True,
    )

    labels = [item["label"] for item in suggestions]
    assert "Usar anexo" in labels
    assert "Buscar em inglês" in labels


def test_attach_to_assistant_metadata_when_web_search_present():
    metadata: dict = {
        "webSearchResearch": {
            "sourceCount": 2,
            "searchStatus": "success",
        },
    }

    ChatWebSearchFollowUpService.attach_to_assistant_metadata(
        metadata,
        tool_context={
            "webSearchPayload": {
                "searchStatus": "success",
                "query": "python asyncio",
            },
        },
        message="pesquise na web sobre python asyncio",
    )

    assert "webSearchFollowUpSuggestions" in metadata
    assert len(metadata["webSearchFollowUpSuggestions"]) >= 3
