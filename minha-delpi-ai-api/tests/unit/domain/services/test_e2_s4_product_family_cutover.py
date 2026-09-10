"""E2.S4 — product-family cutover dial (default OFF) + TU→intent mapper."""

from __future__ import annotations

from unittest.mock import patch

from app.domain.services.chat_conversational_intelligence_flag_service import (
    ChatConversationalIntelligenceFlagService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_turn_understanding_service import ChatTurnUnderstandingService
from app.domain.services.turn_understanding_authority_shadow_service import (
    TurnUnderstandingAuthorityShadowService,
)
from app.domain.services.turn_understanding_product_intent_mapper_service import (
    TurnUnderstandingProductIntentMapperService,
)


def test_product_family_cutover_dial_defaults_off() -> None:
    assert ChatConversationalIntelligenceFlagService.product_family_cutover_enabled() is False


def test_mapper_stock_short_and_synonym() -> None:
    assert (
        TurnUnderstandingProductIntentMapperService.from_message(
            "qual o estoque do produto 10080001?"
        )
        == "stock"
    )
    assert (
        TurnUnderstandingProductIntentMapperService.from_message(
            "saldo disponível do 10080001"
        )
        == "stock"
    )


def test_mapper_compound_multi_scope() -> None:
    message = (
        "1. estoque do 10080001\n"
        "2. fornecedores desse produto\n"
        "3. envia resumo por e-mail"
    )
    assert TurnUnderstandingProductIntentMapperService.from_message(message) == "multi_scope"


def test_mapper_negative_smalltalk_returns_none() -> None:
    assert TurnUnderstandingProductIntentMapperService.from_message("oi, tudo bem?") is None


def test_detect_unchanged_when_cutover_off() -> None:
    message = "qual o estoque do produto 10080001?"
    legacy = ChatProductQueryIntentService.detect(message, force_legacy=True)
    assert ChatProductQueryIntentService.detect(message) == legacy == "stock"


def test_detect_uses_mapper_when_cutover_on() -> None:
    message = "saldo disponível do 10080001"
    with patch.object(
        ChatConversationalIntelligenceFlagService,
        "product_family_cutover_enabled",
        return_value=True,
    ):
        assert ChatProductQueryIntentService.detect(message) == "stock"


def test_detect_falls_back_to_legacy_when_mapper_empty() -> None:
    message = "visão completa do produto 10080001"
    with patch.object(
        ChatConversationalIntelligenceFlagService,
        "product_family_cutover_enabled",
        return_value=True,
    ):
        # Mapper may miss "visão completa" → legacy still answers.
        assert ChatProductQueryIntentService.detect(message)


def test_authority_shadow_reports_cutover_false_by_default() -> None:
    contract = ChatTurnUnderstandingService.analyze(
        "qual o estoque do produto 10080001?"
    )
    shadow = TurnUnderstandingAuthorityShadowService.compare(
        "qual o estoque do produto 10080001?",
        contract,
    )
    assert shadow is not None
    assert shadow["cutover"] is False
    assert shadow["candidateProductIntent"] == "stock"
    assert shadow["productIntent"] == "stock"
    assert shadow["agreeProduct"] is True


def test_authority_shadow_cutover_flag_when_dial_on() -> None:
    contract = ChatTurnUnderstandingService.analyze(
        "qual o estoque do produto 10080001?"
    )
    with patch.object(
        ChatConversationalIntelligenceFlagService,
        "product_family_cutover_enabled",
        return_value=True,
    ):
        shadow = TurnUnderstandingAuthorityShadowService.compare(
            "qual o estoque do produto 10080001?",
            contract,
        )
    assert shadow is not None
    assert shadow["cutover"] is True
