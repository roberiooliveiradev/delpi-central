from unittest.mock import patch

from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService


def test_matches_web_search_triggers():
    assert ChatWebSearchIntentService.matches("pesquise na internet sobre python")


def test_extract_query_strips_deep_search_phrase():
    query = ChatWebSearchIntentService.extract_query(
        "pesquisa profunda na web sobre NR-12"
    )

    assert "profunda" not in query.lower()
    assert "nr-12" in query.lower() or "nr 12" in query.lower()


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


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_should_use_web_for_weather_without_explicit_request(_enabled):
    message = "qual a temperatura de amanha?"

    assert ChatWebSearchIntentService.should_use_web_for_public_facts(message)
    assert ChatWebSearchIntentService.should_use_web_research(message)
    assert ChatWebSearchIntentService.matches(message)
    assert not ChatWebSearchIntentService.is_explicit_request(message)


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_resolve_public_fact_returns_web_search_tool(_enabled):
    result = ChatWebSearchIntentService.resolve("qual a temperatura de amanha?")

    assert result is not None
    assert result["name"] == "web_search"
    assert result["arguments"].get("searchTrigger") == "public_fact"
    assert "temperatura" in result["arguments"]["query"]


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_public_fact_skips_operational_product_question(_enabled):
    message = "qual a temperatura do produto 10080001 no estoque?"

    assert not ChatWebSearchIntentService.should_use_web_for_public_facts(message)


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_should_try_web_after_empty_rag_for_capital_question(_enabled):
    message = "qual a capital da frança?"

    assert not ChatWebSearchIntentService.should_use_web_research(message)
    assert ChatWebSearchIntentService.should_try_web_after_empty_rag(message)


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_should_not_try_post_rag_when_upfront_web_would_run(_enabled):
    message = "qual a temperatura de amanha?"

    assert ChatWebSearchIntentService.should_use_web_research(message)
    assert not ChatWebSearchIntentService.should_try_web_after_empty_rag(message)


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_resolve_post_rag_fallback_returns_web_search_tool(_enabled):
    result = ChatWebSearchIntentService.resolve_for_post_rag_fallback(
        "qual a capital da frança?"
    )

    assert result is not None
    assert result["name"] == "web_search"
    assert result["arguments"].get("searchTrigger") == "post_rag_fallback"
    assert "capital" in result["arguments"]["query"]


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_post_rag_fallback_skips_rewrite_task(_enabled):
    assert not ChatWebSearchIntentService.should_try_web_after_empty_rag(
        "reescreva este paragrafo"
    )


@patch.object(ChatWebSearchIntentService, "is_feature_enabled", return_value=True)
def test_extract_query_post_rag_fallback_separates_suffix(_enabled):
    query = ChatWebSearchIntentService.extract_query("qual a capital da frança?")

    assert "franca dados atuais internet" in query
    assert "francadados" not in query
