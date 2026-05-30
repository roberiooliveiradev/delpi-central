from app.infrastructure.content.content_service import ContentService


def test_load_capabilities_json():
    data = ContentService.load_json("assistant/capabilities")
    assert data.get("intro")
    assert data.get("sections", {}).get("platformTools")


def test_load_api_path_labels():
    data = ContentService.load_json("labels/api_paths")
    paths = {item["path"] for item in (data.get("pathLabels") or [])}
    assert len(paths) >= 80
    assert "/commercial/proposals" in paths
    assert "/production/oee/series" in paths
    assert "/production/eficiencia-fabril/dashboard" in paths
    assert "/system/tables/{tablename}/schema" in paths
    assert "/commercial/billing" not in paths
    assert "/chat/sessions" not in paths


def test_stream_session_title_default():
    assert ContentService.stream().get("sessionTitleDefault") == "Nova conversa"


def test_load_external_action_responses():
    data = ContentService.load_json("assistant/external_action_responses")
    assert data["sql"]["defaultTitle"] == "Consulta SQL"
    assert data["productionSchedule"]["titleTodayFallback"]
    assert len(data["temporal"]["weekdays"]) == 7
    assert len(data["temporal"]["months"]) == 12


def test_load_skills_catalog():
    data = ContentService.load_json("skills/catalog")
    assert len(data.get("skills") or []) >= 2
    assert data["skills"][0].get("key")


def test_load_utility_answers():
    data = ContentService.load_json("assistant/utility_answers")
    assert data["responses"]["current_year"]
    assert len(data["patterns"]["current_time"]) >= 10
