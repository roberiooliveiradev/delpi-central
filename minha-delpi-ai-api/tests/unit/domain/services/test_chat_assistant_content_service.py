from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


def test_loads_stream_activity_phase_groups():
    label = ChatAssistantContentService.get_mapping("stream", "activity", "phaseGroups").get(
        "tools"
    )

    assert label == "Consultando"


def test_sql_error_maps_to_error_handling_message():
    summary = ChatAssistantContentService.get_error_type(
        "sql_syntax_error",
        "userMessage",
    )

    assert "sintaxe" in summary.lower()
