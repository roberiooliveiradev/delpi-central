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


def test_stream_playbook_status_keys():
    stream = ContentService.stream()
    assert stream.get("statusUnderstandingQuestion")
    assert stream.get("statusAssemblingDirectAnswer")
    assert stream.get("cancelledStatusFriendly")


def test_personality_playbook_content():
    playbook = ContentService.personality_playbook()
    assert playbook.get("persona", {}).get("goldenRule")
    assert len(playbook.get("homeStarters") or []) >= 4
    assert len(playbook.get("feedbackReasons") or []) >= 5
    assert playbook.get("followUpQueries", {}).get("Ver estoque")


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
    assert data["responses"]["current_month"]
    assert len(data["patterns"]["current_time"]) >= 10


def test_load_capabilities_rich_examples():
    data = ContentService.load_json("assistant/capabilities")
    assert data.get("richExamples", {}).get("product360")
    assert len(data.get("combinedQuestions") or []) >= 3
