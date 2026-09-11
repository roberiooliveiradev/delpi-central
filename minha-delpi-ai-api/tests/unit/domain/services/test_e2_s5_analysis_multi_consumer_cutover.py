"""E2.S5 full — analysis multi-consumer cutover via ChatAnalysisIntentService.is_*."""

from __future__ import annotations

from unittest.mock import patch

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_conversational_intelligence_flag_service import (
    ChatConversationalIntelligenceFlagService,
)


def _tool_history() -> list[dict]:
    return [
        {
            "role": "assistant",
            "content": "Roteiro do produto",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260142/guide",
                        },
                    }
                ]
            },
        }
    ]


def test_data_interpretation_dial_default_on() -> None:
    assert (
        ChatConversationalIntelligenceFlagService.data_interpretation_family_cutover_enabled()
        is True
    )


def test_comparison_p0_and_sibling() -> None:
    assert ChatAnalysisIntentService.is_comparison_or_insight_request(
        "compara o estoque deste mês com o mês passado"
    )
    assert ChatAnalysisIntentService.is_comparison_or_insight_request(
        "qual a diferença entre os dois produtos"
    )


def test_comparison_negative_product_fetch() -> None:
    assert not ChatAnalysisIntentService.is_comparison_or_insight_request(
        "qual o estoque do produto 10080001?"
    )


def test_comparison_dials_off_equals_legacy() -> None:
    message = "compara o estoque deste mês com o mês passado"
    with patch.object(
        ChatConversationalIntelligenceFlagService,
        "compare_explain_family_cutover_enabled",
        return_value=False,
    ):
        off = ChatAnalysisIntentService.is_comparison_or_insight_request(message)
    on = ChatAnalysisIntentService.is_comparison_or_insight_request(message)
    assert off is True and on is True


def test_data_interpretation_requires_history() -> None:
    assert not ChatAnalysisIntentService.is_data_interpretation_request(
        "explique os dados acima",
        [],
    )
    assert ChatAnalysisIntentService.is_data_interpretation_request(
        "explique os dados acima",
        _tool_history(),
    )


def test_data_interpretation_tu_assist_with_tool_data() -> None:
    history = _tool_history()
    # legacy short-command path already covers "resume"; ensure dial ON still True
    assert ChatAnalysisIntentService.is_data_interpretation_request("resume", history)
