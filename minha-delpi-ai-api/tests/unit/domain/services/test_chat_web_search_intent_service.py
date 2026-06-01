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
