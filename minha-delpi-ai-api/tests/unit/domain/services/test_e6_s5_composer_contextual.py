"""E6.S5 — composer contextual: entities, allowlist, cache (sem LLM por tecla)."""

from __future__ import annotations

from app.domain.services.chat_composer_route_question_suggestion_service import (
    ChatComposerRouteQuestionSuggestionService,
)


def setup_function() -> None:
    ChatComposerRouteQuestionSuggestionService.clear_cache()


def test_e6_s5_entity_fills_product_code_in_stock_query():
    suggestions = ChatComposerRouteQuestionSuggestionService.suggest(
        "estoque do produto 10080001",
        use_cache=False,
    )
    assert suggestions
    assert any("10080001" in str(item.get("query") or "") for item in suggestions)


def test_e6_s5_allowlist_drops_stock_group_when_only_drawing_allowed():
    open_suggestions = ChatComposerRouteQuestionSuggestionService.suggest(
        "estoque",
        use_cache=False,
    )
    assert open_suggestions  # sem allowlist, templates sobem (se houver match sem product)

    filtered = ChatComposerRouteQuestionSuggestionService.suggest(
        "estoque",
        allowed_action_ids=["ext.products.drawing_validate", "drawing.analyse"],
        use_cache=False,
    )
    assert not any(
        str(item.get("groupId") or "") == "product_stock" for item in filtered
    )


def test_e6_s5_allowlist_keeps_drawing_group():
    suggestions = ChatComposerRouteQuestionSuggestionService.suggest(
        "analise",
        allowed_action_ids=["ext.drawing.validate_pdf"],
        use_cache=False,
    )
    assert suggestions
    assert any("desenho" in str(item.get("query") or "").casefold() for item in suggestions)


def test_e6_s5_cache_returns_same_payload_for_same_draft():
    first = ChatComposerRouteQuestionSuggestionService.suggest("analise")
    second = ChatComposerRouteQuestionSuggestionService.suggest("analise")
    assert first == second
    assert first


def test_e6_s5_cache_key_differs_by_allowlist():
    a = ChatComposerRouteQuestionSuggestionService.suggest(
        "analise",
        allowed_action_ids=["drawing.a"],
    )
    b = ChatComposerRouteQuestionSuggestionService.suggest(
        "analise",
        allowed_action_ids=["stock.b"],
    )
    # drawing allowlist mantém; stock allowlist remove drawing group
    assert a
    assert not any(
        str(item.get("groupId") or "") == "drawing_analysis" for item in b
    )


def test_e6_s5_short_draft_still_empty():
    assert ChatComposerRouteQuestionSuggestionService.suggest("ab") == []


def test_e6_s5_does_not_auto_execute_tools():
    """Sugestões são só queries textuais — sem actionId executável no composer."""

    suggestions = ChatComposerRouteQuestionSuggestionService.suggest(
        "analise",
        use_cache=False,
    )
    assert suggestions
    assert all("actionId" not in item for item in suggestions)
