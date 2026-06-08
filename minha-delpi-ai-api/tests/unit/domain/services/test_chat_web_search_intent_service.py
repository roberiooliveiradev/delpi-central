from unittest.mock import patch

from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService


def test_matches_web_search_triggers():
    assert ChatWebSearchIntentService.matches("pesquise na internet sobre python")


def test_extract_query_strips_trigger_phrase():
    query = ChatWebSearchIntentService.extract_query(
        "pesquise na internet sobre inflacao 2026"
    )

    assert "internet" not in query
    assert "inflacao" in query or "2026" in query


def test_extract_query_strips_company_prefix():
    query = ChatWebSearchIntentService.extract_query(
        "pesquise na internet sobre a empresa TYCO"
    )

    assert query == "tyco"


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_resolve_returns_tool_selection(_enabled):
    result = ChatWebSearchIntentService.resolve(
        "busque na web sobre clima em sao paulo"
    )

    assert result is not None
    assert result["name"] == "web_search"
    assert result["arguments"]["query"]


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=False)
def test_resolve_disabled_when_feature_off(_enabled):
    assert ChatWebSearchIntentService.resolve("pesquise na internet sobre x") is None


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=False)
def test_blocks_external_action_when_disabled(_enabled):
    assert ChatWebSearchIntentService.blocks_external_action_selection(
        "pesquise na internet sobre python"
    )


def test_product_search_heuristic_ignores_explicit_web_request():
    from app.application.services.external_actions.external_action_selection_service import (
        ExternalActionSelectionService,
    )

    service = ExternalActionSelectionService(None)
    normalized = "pesquise na web sobre delpi conexoes eletricas"

    assert not service._looks_like_product_search(normalized)


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_blocks_external_action_when_enabled(_enabled):
    assert ChatWebSearchIntentService.blocks_external_action_selection(
        "pesquise na internet sobre python"
    )


@patch.object(ChatWebSearchIntentService, "is_auto_augment_enabled", return_value=True)
@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_should_augment_open_question_about_topic(_feature, _augment):
    message = "o que vc pensa sobre o Brasil?"

    assert ChatWebSearchIntentService.should_augment_with_web(message)
    assert ChatWebSearchIntentService.should_use_web_research(message)
    assert not ChatWebSearchIntentService.is_explicit_request(message)


@patch.object(ChatWebSearchIntentService, "is_auto_augment_enabled", return_value=True)
@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_extract_query_for_augment_strips_opinion_prefix(_feature, _augment):
    query = ChatWebSearchIntentService.extract_query(
        "o que vc pensa sobre o Brasil?"
    )

    assert "pensa" not in query
    assert "brasil" in query


@patch.object(ChatWebSearchIntentService, "is_auto_augment_enabled", return_value=True)
@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_resolve_augment_returns_web_search_tool(_feature, _augment):
    result = ChatWebSearchIntentService.resolve("o que vc acha do mercado de energia?")

    assert result is not None
    assert result["name"] == "web_search"
    assert result["arguments"].get("searchTrigger") == "auto_augment"
    assert result["arguments"]["query"]


@patch.object(ChatWebSearchIntentService, "is_auto_augment_enabled", return_value=True)
@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_should_not_augment_capabilities_question(_feature, _augment):
    assert not ChatWebSearchIntentService.should_augment_with_web("o que voce faz?")


@patch.object(ChatWebSearchIntentService, "is_auto_augment_enabled", return_value=False)
@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_should_not_augment_when_flag_disabled(_feature, _augment):
    assert not ChatWebSearchIntentService.should_augment_with_web(
        "o que vc pensa sobre o Brasil?"
    )
