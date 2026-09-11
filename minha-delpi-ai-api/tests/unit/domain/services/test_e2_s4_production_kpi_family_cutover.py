"""E2.S4 — production/KPI family cutover (superseded by J-R9 single owner)."""

from __future__ import annotations

from unittest.mock import patch

from app.domain.services.chat_conversational_intelligence_flag_service import (
    ChatConversationalIntelligenceFlagService,
)
from app.domain.services.chat_department_kpi_intent_service import (
    ChatDepartmentKpiIntentService,
)
from app.domain.services.chat_production_operational_intent_service import (
    ChatProductionOperationalIntentService,
    ProductionOperationalIntentKind,
)
from app.domain.services.chat_turn_understanding_service import ChatTurnUnderstandingService
from app.domain.services.turn_understanding_authority_shadow_service import (
    TurnUnderstandingAuthorityShadowService,
)
from app.domain.services.turn_understanding_kpi_intent_mapper_service import (
    TurnUnderstandingKpiIntentMapperService,
)
from app.domain.services.turn_understanding_production_intent_mapper_service import (
    TurnUnderstandingProductionIntentMapperService,
)


def test_production_and_kpi_dials_default_on_for_canary() -> None:
    assert ChatConversationalIntelligenceFlagService.production_family_cutover_enabled() is True
    assert ChatConversationalIntelligenceFlagService.kpi_family_cutover_enabled() is True
    assert ChatConversationalIntelligenceFlagService.product_family_cutover_enabled() is True


def test_j_r9_production_mapper_does_not_emit_kind() -> None:
    assert (
        TurnUnderstandingProductionIntentMapperService.from_message(
            "programação de produção hoje"
        )
        is None
    )
    assert TurnUnderstandingProductionIntentMapperService.from_message("ops abertas") is None
    assert (
        TurnUnderstandingProductionIntentMapperService.from_message(
            "Quais itens mais consumidos no mês?"
        )
        is None
    )


def test_j_r9_production_live_resolve_none_legacy_parity_via_force() -> None:
    message = "programação de produção hoje"
    assert ChatProductionOperationalIntentService.resolve(message) is None
    assert (
        ChatProductionOperationalIntentService.resolve(message, force_legacy=True)
        == ProductionOperationalIntentKind.SCHEDULE_TODAY
    )


def test_j_r9_kpi_mapper_and_live_resolve_demoted() -> None:
    assert (
        TurnUnderstandingKpiIntentMapperService.from_message(
            "qual a meta comercial deste mês"
        )
        is None
    )
    assert ChatDepartmentKpiIntentService.resolve("qual o ebitda do último trimestre") is None
    legacy = ChatDepartmentKpiIntentService.resolve(
        "qual o ebitda do último trimestre",
        force_legacy=True,
    )
    assert legacy is not None
    assert legacy.path_token == "ebitda"


def test_kpi_mapper_negative_product_code() -> None:
    assert (
        TurnUnderstandingKpiIntentMapperService.from_message(
            "estoque do produto 10080001"
        )
        is None
    )


def test_authority_shadow_candidates_production_kpi_demoted() -> None:
    contract = ChatTurnUnderstandingService.analyze("programação de produção hoje")
    shadow = TurnUnderstandingAuthorityShadowService.compare(
        "programação de produção hoje",
        contract,
    )
    assert shadow is not None
    assert shadow["cutoverProduction"] is True
    assert shadow["cutoverKpi"] is True
    # J-R9 — mapper candidates no longer materialize kind/catalogToken.
    assert shadow.get("candidateProductionKind") is None
    assert shadow.get("candidateKpi") is None


def test_force_legacy_ignores_j_r9_gate_for_parity() -> None:
    message = "programação de produção hoje"
    with patch.object(
        ChatConversationalIntelligenceFlagService,
        "production_family_cutover_enabled",
        return_value=False,
    ), patch.object(
        ChatConversationalIntelligenceFlagService,
        "kpi_family_cutover_enabled",
        return_value=False,
    ):
        assert (
            ChatProductionOperationalIntentService.resolve(message, force_legacy=True)
            == ProductionOperationalIntentKind.SCHEDULE_TODAY
        )
        assert (
            ChatDepartmentKpiIntentService.resolve(
                "qual o ebitda do último trimestre",
                force_legacy=True,
            ).path_token
            == "ebitda"
        )
