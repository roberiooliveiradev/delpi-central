"""E2.S5 — generic intent/router cutover (no_tool / presentation / compare_explain)."""

from __future__ import annotations

from unittest.mock import patch

from app.domain.services.chat_conversational_intelligence_flag_service import (
    ChatConversationalIntelligenceFlagService,
)
from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.turn_understanding_generic_intent_mapper_service import (
    TurnUnderstandingGenericIntentMapperService,
)


def test_generic_dials_default_on() -> None:
    assert ChatConversationalIntelligenceFlagService.no_tool_family_cutover_enabled() is True
    assert ChatConversationalIntelligenceFlagService.presentation_family_cutover_enabled() is True
    assert (
        ChatConversationalIntelligenceFlagService.compare_explain_family_cutover_enabled()
        is True
    )


def test_mapper_no_tool_smalltalk() -> None:
    signals = TurnUnderstandingGenericIntentMapperService.from_message("oi, tudo bem?")
    assert signals.no_tool is False
    assert signals.presentation_view is None


def test_mapper_presentation_table() -> None:
    signals = TurnUnderstandingGenericIntentMapperService.from_message(
        "mostra isso em tabela"
    )
    assert signals.presentation_view == "table"


def test_mapper_presentation_chart_sibling() -> None:
    signals = TurnUnderstandingGenericIntentMapperService.from_message(
        "gera um gráfico disso"
    )
    assert signals.presentation_view == "chart"


def test_classify_presentation_format_refinement_agree() -> None:
    route = ChatIntentRouterService.classify("mostra isso em tabela")
    assert route.intent == "follow_up"
    assert route.sub_intent == "format_refinement"
    assert "tu_presentation_agree" in route.flags
    assert "tu_view:table" in route.flags


def test_classify_presentation_text_task_aligns_view() -> None:
    route = ChatIntentRouterService.classify("quero ver em tabela")
    assert route.intent == "text_task"
    assert route.sub_intent == "table"
    assert "tu_presentation" in route.flags


def test_classify_no_tool_agree_flag_on_smalltalk() -> None:
    route = ChatIntentRouterService.classify("oi, tudo bem?")
    assert route.intent == "small_talk"
    assert "tu_no_tool_agree" in route.flags


def test_classify_negative_operational_not_smalltalk() -> None:
    route = ChatIntentRouterService.classify("qual o estoque do produto 10080001?")
    assert route.intent != "small_talk"
    assert "tu_no_tool_agree" not in route.flags


def test_dials_off_equals_legacy_presentation() -> None:
    message = "quero ver em tabela"
    with patch.object(
        ChatConversationalIntelligenceFlagService,
        "presentation_family_cutover_enabled",
        return_value=False,
    ), patch.object(
        ChatConversationalIntelligenceFlagService,
        "no_tool_family_cutover_enabled",
        return_value=False,
    ), patch.object(
        ChatConversationalIntelligenceFlagService,
        "compare_explain_family_cutover_enabled",
        return_value=False,
    ):
        off = ChatIntentRouterService.classify(message)
    on = ChatIntentRouterService.classify(message)
    assert off.intent == on.intent == "text_task"
    assert "tu_presentation" not in off.flags
    assert off.sub_intent == "to_table"
    assert on.sub_intent == "table"
