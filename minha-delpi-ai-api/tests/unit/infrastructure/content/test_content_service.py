from app.infrastructure.content.content_service import ContentService


def test_load_capabilities_json():
    data = ContentService.load_json("assistant/capabilities")
    assert data.get("intro")
    assert data.get("sections", {}).get("platformTools")


def test_load_api_path_labels():
    data = ContentService.load_json("labels/api_paths")
    assert len(data.get("pathLabels") or []) > 10


def test_stream_session_title_default():
    assert ContentService.stream().get("sessionTitleDefault") == "Nova conversa"


def test_load_external_action_responses():
    data = ContentService.load_json("assistant/external_action_responses")
    assert data["sql"]["defaultTitle"] == "Consulta SQL"
    assert data["productionSchedule"]["titleTodayFallback"]
    assert len(data["temporal"]["weekdays"]) == 7
