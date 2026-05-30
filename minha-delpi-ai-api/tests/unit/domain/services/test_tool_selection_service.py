from app.domain.services.tool_selection_service import ToolSelectionService


def test_selects_current_user_tool():
    service = ToolSelectionService()

    result = service.select_tools("Quem sou eu?")

    assert result[0]["name"] == "get_current_user"


def test_selects_allowed_apps_tool():
    service = ToolSelectionService()

    result = service.select_tools("Quais aplicativos eu tenho acesso?")

    assert result[0]["name"] == "get_allowed_apps"


def test_selects_allowed_routes_tool():
    service = ToolSelectionService()

    result = service.select_tools("Quais menus disponíveis eu posso acessar?")

    assert result[0]["name"] == "get_allowed_routes"


def test_selects_no_tool_for_generic_question():
    service = ToolSelectionService()

    result = service.select_tools("O que é a Minha DELPI?")

    assert result == []


def test_selects_web_search_when_enabled(monkeypatch):
    from app.domain.services import chat_web_search_intent_service as module

    monkeypatch.setattr(
        module.ChatWebSearchIntentService,
        "is_feature_enabled",
        lambda: True,
    )

    service = ToolSelectionService()
    result = service.select_tools("pesquise na internet sobre python")

    assert result[-1]["name"] == "web_search"
