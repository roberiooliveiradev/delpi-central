"""E2.S4 — product-family cutover (superseded by J-R9 single owner)."""

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


def test_product_family_cutover_dial_defaults_on_for_product_canary() -> None:
    assert ChatConversationalIntelligenceFlagService.product_family_cutover_enabled() is True


def test_j_r9_mapper_does_not_emit_facet() -> None:
    assert (
        TurnUnderstandingProductIntentMapperService.from_message(
            "qual o estoque do produto 10080001?"
        )
        is None
    )
    assert (
        TurnUnderstandingProductIntentMapperService.from_message(
            "saldo disponível do 10080001"
        )
        is None
    )


def test_j_r9_mapper_compound_does_not_emit_multi_scope() -> None:
    message = (
        "1. estoque do 10080001\n"
        "2. fornecedores desse produto\n"
        "3. envia resumo por e-mail"
    )
    assert TurnUnderstandingProductIntentMapperService.from_message(message) is None


def test_mapper_negative_smalltalk_returns_none() -> None:
    assert TurnUnderstandingProductIntentMapperService.from_message("oi, tudo bem?") is None


def test_mapper_negative_rag_policy_not_purchases() -> None:
    assert (
        TurnUnderstandingProductIntentMapperService.from_message(
            "o que diz a política de compras?"
        )
        is None
    )


def test_detect_falls_back_without_mapper_authority() -> None:
    message = "saldo disponível do 10080001"
    # Live detect may use legacy/content heuristics; mapper is not the owner.
    assert TurnUnderstandingProductIntentMapperService.from_message(message) is None
    assert ChatProductQueryIntentService.detect(message, force_legacy=True) == "stock"


def test_detect_rag_policy_falls_back_to_legacy_full() -> None:
    message = "o que diz a política de compras?"
    assert ChatProductQueryIntentService.detect(message, force_legacy=True) == "full"
    assert ChatProductQueryIntentService.detect(message) == "full"


def test_authority_shadow_reports_cutover_without_facet_candidate() -> None:
    contract = ChatTurnUnderstandingService.analyze(
        "qual o estoque do produto 10080001?"
    )
    shadow = TurnUnderstandingAuthorityShadowService.compare(
        "qual o estoque do produto 10080001?",
        contract,
    )
    assert shadow is not None
    assert shadow["cutover"] is True
    assert shadow.get("candidateProductIntent") in (None, "", "NONE", "None")


def test_authority_shadow_cutover_false_when_dial_off() -> None:
    contract = ChatTurnUnderstandingService.analyze(
        "qual o estoque do produto 10080001?"
    )
    with patch.object(
        ChatConversationalIntelligenceFlagService,
        "product_family_cutover_enabled",
        return_value=False,
    ):
        shadow = TurnUnderstandingAuthorityShadowService.compare(
            "qual o estoque do produto 10080001?",
            contract,
        )
        assert shadow is not None
        assert shadow["cutover"] is False
